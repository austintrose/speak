/* Austin Rose CS529 Spring 2015 Project 1 */

/* Use the newer ALSA API */
#define ALSA_PCM_NEW_HW_PARAMS_API

#include <stdio.h>
#include <math.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <alsa/asoundlib.h>
#include "record.h"

audio_segment_t *current_segment = 0;
thresholds_t *thresholds = 0;
int segments_analyzed = 0;
int keep_recording = 1;
snd_pcm_t *handle;
snd_pcm_uframes_t frames = BYTES_PER_10MS;
int silence_segments = 10;
unsigned char *buffer;

audio_segment_t *N1, *N2;
audio_segment_t *earliest;
audio_segment_t *cursor;

int main() {
    init();
    do_recording();
    cleanup();
    return 0;
}

void do_recording() {
    segments_analyzed = 0;
    detection_state_t current_state = FIND_N1;
    unsigned int peaks_found_before_N1 = 0;
    unsigned int segments_checked_after_N2 = 0;
    unsigned int peaks_found_after_N2 = 0;
    unsigned int segments_waited_in_reset = 0;

    keep_recording = 1;
    while (keep_recording) {

        fill_buffer();

        /* Analyze segment */
        audio_segment_t *new_segment = analyze_segment(buffer);
        new_segment->previous = current_segment;

        /* Write raw audio and data files */
        // write_audio(new_segment);

        /* Advance pointer */
        if (current_segment) {
            current_segment->next = new_segment;
        }
        current_segment = new_segment;

        /* Don't proceed if we're not ready to detect endpoints yet */
        if (segments_analyzed < silence_segments) {
            segments_analyzed++;
            continue;
        } else if (segments_analyzed == silence_segments) {
            segments_analyzed++;
            compute_thresholds();
            continue;
        }

        /* Detect some end points! */
        int i;
        switch (current_state) {
        case FIND_N1:
            /* Mark a potential N1 if energy is above lower threshold */
            if (current_segment->energy > thresholds->ITL) {
                N1 = current_segment;
                current_state = VERIFY_N1;
            }

            break;

        case VERIFY_N1:
            /* Accept the N1 we marked if the energy is above upper threshold */
            if (current_segment->energy > thresholds->ITU) {
                current_state = EXPAND_N1;

            } else {
                /* Find a new N1 if the energy is back below lower threshold */
                if (current_segment->energy <= thresholds->ITL) {
                    current_state = FIND_N1;
                }
                break;
            }

        case EXPAND_N1:
            /* Reduce N1 by up to 250ms based on ZCR before it */
            cursor = current_segment;
            for (i = 0; i < 25; i++) {
                if (cursor->zero_cross_rate > thresholds->IZCT) {
                    peaks_found_before_N1++;
                    earliest = cursor;
                }

                cursor = cursor->previous;
            }

            if (peaks_found_before_N1 >= 3) {
                N1 = earliest;
            }

            current_state = FIND_N2;

        case FIND_N2:
            /* Mark a potential N2 if energy is below upper threshold */
            if (current_segment->energy <= thresholds->ITU) {
                current_state = VERIFY_N2;
            }
            break;

        case VERIFY_N2:
            /* Accept the N2 we marked if the energy is below lower threshold */
            if (current_segment->energy <= thresholds->ITL) {
                N2 = current_segment;
                current_state = EXPAND_N2;

            /* Find a new N2 if the energy is back above upper threshold */
            } else if (current_segment->energy > thresholds->ITU) {
                current_state = FIND_N2;
            }

            break;

        case EXPAND_N2:
            if (segments_checked_after_N2++ < 25) {
                if (current_segment->zero_cross_rate > thresholds->IZCT) {
                    if (++peaks_found_after_N2 >= 3) {
                        N2 = current_segment;
                    }
                }
            }

            else {
                current_state = RESET;
            }

            break;

        case RESET:
            if (segments_waited_in_reset++ == 25) {
                current_state = FIND_N1;
                peaks_found_before_N1 = 0;
                segments_checked_after_N2 = 0;
                peaks_found_after_N2 = 0;
                segments_waited_in_reset = 0;
                write_speech(N1, N2);
            }

            break;
        }
    }
}

void fill_buffer() {
    int rc = snd_pcm_readi(handle, buffer, frames);

    if (rc == -EPIPE) {
	exit(1);
        printf("Overrun occurred!\n");
        snd_pcm_prepare(handle);
    } else if (rc < 0) {
	exit(1);
        printf("Error from read: %s.\n", snd_strerror(rc));
    } else if (rc != (int)frames) {
        printf("Short read, read %d frames.\n", rc);
    }
}

audio_segment_t *analyze_segment(unsigned char * seg) {
    audio_segment_t *to_return = (audio_segment_t *)malloc(sizeof(audio_segment_t));

    to_return->raw = (unsigned char *)malloc(frames);

    unsigned long i;
    unsigned char was_above_zero = 0;
    unsigned int energy = 0;
    unsigned int zero_cross_rate = 0;

    for (i = 0; i < frames; i++) {
        unsigned char b = seg[i];
        to_return->raw[i] = b;

        unsigned char mag, now_above_zero;
        if (b > 128) {
            mag = b - 128;
            now_above_zero = 1;
        } else {
            mag = 128 - b;
            now_above_zero = 0;
        }

        energy += mag;

        zero_cross_rate += (now_above_zero != was_above_zero);
        was_above_zero = now_above_zero;
    }

    to_return->energy = energy;
    to_return->zero_cross_rate = zero_cross_rate;

    return to_return;
}

void compute_thresholds() {
    thresholds = (thresholds_t *)malloc(sizeof(thresholds_t));
    cursor = current_segment;

    unsigned long i;
    unsigned int energy[silence_segments];
    unsigned int zero_cross_rate[silence_segments];

    unsigned int IMX = 0;

    for (i = 0; i < silence_segments; i++) {
        if (IMX < cursor->energy) {
            IMX = cursor->energy;
        }

        energy[i] = cursor->energy;
        zero_cross_rate[i] = cursor->zero_cross_rate;

        cursor = cursor->previous;
    }

    double mean_zcr = mean(zero_cross_rate, silence_segments);
    double std_dev_zcr = standard_deviation(zero_cross_rate, silence_segments, mean_zcr);

    /* Zero crossing threshold */
    double IZCT = 20.0; // This is the max we'll allow the threshold
    double measured_IZCT = mean_zcr + (2 * std_dev_zcr);
    if (measured_IZCT < IZCT) {
        IZCT = measured_IZCT;
    }

    double IMN = mean(energy, silence_segments);
    double I1 = 0.03 * (IMX - IMN) + IMN;
    double I2 = 4 * IMN;
    double ITL = (I1 < I2 ? I1 : I2);
    double ITU = 5 * ITL;

    thresholds->IZCT = IZCT;
    thresholds->ITL = ITL;
    thresholds->ITU = ITU;
}

void write_speech(audio_segment_t *n1, audio_segment_t *n2) {
    while (n1 != n2) {
        fwrite(n1->raw, BYTES_PER_10MS, 1, stdout);
        fflush(stdout);
        n1 = n1->next;
    }
}

void interrupt_handler(int sig) {
    keep_recording = 0;
}

double mean(unsigned int data[], unsigned int length) {
    double r = 0;
    unsigned int i;
    for (i = 0; i < length; i++) {
        r += data[i];
    }

    r = r / length;
    return r;
}

double standard_deviation(unsigned int data[], unsigned int length, double mean) {
    double sum_deviation = 0.0;

    unsigned int i;
    for(i = 0; i < length; i++) {
        sum_deviation += (data[i]-mean)*(data[i]-mean);
    }

    return sqrt(sum_deviation/length);
}

void init() {

    /* Register the interrupt handler to stop and process data on ctrl-c */
    signal(SIGINT, interrupt_handler);

    /* Open device for recording */
    int rc = snd_pcm_open(&handle, "default", SND_PCM_STREAM_CAPTURE, 0);
    if (rc < 0) {
        printf("Unable to open device: %s.\nExiting.\n", snd_strerror(rc));
        exit(1);
    }

    /* Allocate a hardware parameters object */
    snd_pcm_hw_params_t *params;
    snd_pcm_hw_params_alloca(&params);

    /* Fill it in with default values */
    snd_pcm_hw_params_any(handle, params);

    int dir;
    snd_pcm_hw_params_set_period_size_near(handle, params, &frames, &dir);
    snd_pcm_hw_params_get_period_size(params, &frames, &dir);

    /* Write the parameters to the driver */
    rc = snd_pcm_hw_params(handle, params);
    if (rc < 0) {
        printf("Unable to set parameters: %s.\nExiting.", snd_strerror(rc));
        exit(1);
    }

    /* Set parameters for this assignment */
    snd_pcm_set_params(
        handle,
        SND_PCM_FORMAT_U8, /* unsigned, 8 bit */
        SND_PCM_ACCESS_RW_INTERLEAVED,
        1, /* channels */
        8000, /* sample rate */
        1, /* allow re-sampling*/
        500000 /* 0.5 sec */
    );

    buffer = (unsigned char *)malloc(frames);
}

void cleanup() {
    free(buffer);

    /* Flush and close device */
    snd_pcm_drain(handle);
    snd_pcm_close(handle);
}
