#define BYTES_PER_10MS 80

typedef enum {
    FIND_N1, VERIFY_N1, EXPAND_N1,
    FIND_N2, VERIFY_N2, EXPAND_N2,
    RESET
} detection_state_t;

typedef struct audio_segment_t {
    unsigned char *raw;
    unsigned int energy;
    unsigned int zero_cross_rate;
    struct audio_segment_t *previous;
    struct audio_segment_t *next;
} audio_segment_t;

typedef struct thresholds_t {
    double ITL;
    double ITU;
    double IZCT;
} thresholds_t;

void fill_buffer(void);
void do_recording(void);
void init_playback(void);
void init(void);
void close_files(void);
void open_files(void);
double standard_deviation(unsigned int *, unsigned int, double);
double mean(unsigned int *, unsigned int);
void interrupt_handler(int);
void write_speech(audio_segment_t *, audio_segment_t *);
void write_audio(audio_segment_t *);
void compute_thresholds(void);
audio_segment_t *analyze_segment(unsigned char *);
void cleanup(void);
