-- Supabase Schema for FalseGrip
-- Run these in the Supabase SQL editor

CREATE TABLE IF NOT EXISTS exercise_definitions (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    exercise_type TEXT NOT NULL,
    is_predefined BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE exercise_definitions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own exercises" ON exercise_definitions FOR ALL USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS workouts (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    workout_date DATE NOT NULL,
    notes TEXT DEFAULT '',
    is_draft BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own workouts" ON workouts FOR ALL USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS workout_exercises (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    workout_id TEXT NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_definition_id TEXT NOT NULL REFERENCES exercise_definitions(id),
    exercise_name TEXT NOT NULL,
    category TEXT NOT NULL,
    exercise_type TEXT NOT NULL,
    order_index INTEGER NOT NULL
);

ALTER TABLE workout_exercises ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own workout exercises" ON workout_exercises FOR ALL USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS workout_sets (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    workout_exercise_id TEXT NOT NULL REFERENCES workout_exercises(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    weight_kg REAL,
    reps INTEGER,
    duration_seconds INTEGER
);

ALTER TABLE workout_sets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own sets" ON workout_sets FOR ALL USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS workout_plans (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    notes TEXT DEFAULT '',
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE workout_plans ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own plans" ON workout_plans FOR ALL USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS workout_plan_exercises (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    workout_plan_id TEXT NOT NULL REFERENCES workout_plans(id) ON DELETE CASCADE,
    exercise_definition_id TEXT NOT NULL REFERENCES exercise_definitions(id),
    exercise_name TEXT NOT NULL,
    category TEXT NOT NULL,
    exercise_type TEXT NOT NULL,
    order_index INTEGER NOT NULL
);

ALTER TABLE workout_plan_exercises ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own plan exercises" ON workout_plan_exercises FOR ALL USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS workout_plan_sets (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    workout_plan_exercise_id TEXT NOT NULL REFERENCES workout_plan_exercises(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    weight_kg REAL,
    reps INTEGER,
    duration_seconds INTEGER
);

ALTER TABLE workout_plan_sets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own plan sets" ON workout_plan_sets FOR ALL USING (auth.uid() = user_id);
