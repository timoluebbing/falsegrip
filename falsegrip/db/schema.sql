PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS exercise_definitions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    exercise_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workouts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    workout_date TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    is_draft BOOLEAN DEFAULT FALSE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workout_exercises (
    id TEXT PRIMARY KEY,
    workout_id TEXT NOT NULL,
    exercise_definition_id TEXT NOT NULL,
    exercise_name TEXT NOT NULL,
    category TEXT NOT NULL,
    exercise_type TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_definition_id) REFERENCES exercise_definitions(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS workout_sets (
    id TEXT PRIMARY KEY,
    workout_exercise_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    weight_kg REAL,
    reps INTEGER,
    duration_seconds INTEGER,
    FOREIGN KEY (workout_exercise_id) REFERENCES workout_exercises(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workout_plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workout_plan_exercises (
    id TEXT PRIMARY KEY,
    workout_plan_id TEXT NOT NULL,
    exercise_definition_id TEXT NOT NULL,
    exercise_name TEXT NOT NULL,
    category TEXT NOT NULL,
    exercise_type TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    FOREIGN KEY (workout_plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_definition_id) REFERENCES exercise_definitions(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS workout_plan_sets (
    id TEXT PRIMARY KEY,
    workout_plan_exercise_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    weight_kg REAL,
    reps INTEGER,
    duration_seconds INTEGER,
    FOREIGN KEY (workout_plan_exercise_id) REFERENCES workout_plan_exercises(id) ON DELETE CASCADE
);
