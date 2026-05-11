-- Migration: Add status and error columns to quiz_attempts
-- Run this if you already have the quiz_attempts table

-- Add status column if not exists
ALTER TABLE quiz_attempts 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'generating';

-- Add error column if not exists
ALTER TABLE quiz_attempts 
ADD COLUMN IF NOT EXISTS error VARCHAR(500);

-- Make questions column nullable
ALTER TABLE quiz_attempts 
ALTER COLUMN questions DROP NOT NULL;

-- Update existing records to have status 'ready' if they have questions
UPDATE quiz_attempts 
SET status = 'ready' 
WHERE questions IS NOT NULL AND status = 'generating';
