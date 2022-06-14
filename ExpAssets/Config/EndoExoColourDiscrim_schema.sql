CREATE TABLE participants (
    id integer primary key autoincrement not null,
    userhash text not null,
    gender text not null,
    age integer not null, 
    handedness text not null,
    created text not null
);

CREATE TABLE trials (
    id integer primary key autoincrement not null,
    participant_id integer not null references participants(id),
    block_num integer not null,
    trial_num integer not null,
    fix_duration integer not null,
    ctoa integer not null,
    cue_valid text not null,
    signal_intensity text not null,
    target_rgb text not null,
    response_rgb text not null,
    detection_rt text not null,
    discrimination_error text not null,
    discrimination_rt text not null
);
