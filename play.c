/* Austin Rose CS529 Spring 2015 Project 1 */

/* Use the newer ALSA API */
#define ALSA_PCM_NEW_HW_PARAMS_API

#include <alsa/asoundlib.h>

int main() {
    int i;

    /* Open PCM device for playback */
    snd_pcm_t *handle;
    int rc = snd_pcm_open(&handle, "default", SND_PCM_STREAM_PLAYBACK, 0);
    if (rc < 0) {
        printf("Unable to open device: %s.\nExiting.\n", snd_strerror(rc));
        exit(1);
    }

    /* Allocate a hardware parameters object */
    snd_pcm_hw_params_t *params;
    snd_pcm_hw_params_alloca(&params);

    /* Fill it in with default values */
    snd_pcm_hw_params_any(handle, params);

    /* Set period size to 32 frames */
    snd_pcm_uframes_t frames = 32;
    snd_pcm_hw_params_set_period_size_near(handle, params, &frames, &i);

    /* Write the parameters to the driver */
    rc = snd_pcm_hw_params(handle, params);
    if (rc < 0) {
        printf("Unable to set parameters: %s.\nExiting.\n", snd_strerror(rc));
        exit(1);
    }

    /* Use a buffer large enough to hold one period */
    snd_pcm_hw_params_get_period_size(params, &frames, &i);
    int size = frames;
    unsigned char *buffer = (unsigned char *)malloc(size);

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

    while (1) {

        rc = read(0, buffer, size);

        if (rc > 0) {
	    rc = snd_pcm_writei(handle, buffer, frames);
        }

        if (rc == -EPIPE) {
            snd_pcm_prepare(handle);
            break;
        } else if (rc < 0) {
            break;
        }  
    }

    /* Clean up */
    snd_pcm_drain(handle);
    snd_pcm_close(handle);
    free(buffer);

    return 0;
}

