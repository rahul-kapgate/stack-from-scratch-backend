import dotenv from "dotenv";
dotenv.config();

function getEnv(key, fallback) {
  const value = process.env[key] ?? fallback;
  if (value === undefined) {
    throw new Error(`Missing required env var: ${key}`);
  }
  return value;
}

export const ENV = {
  NODE_ENV: process.env.NODE_ENV || 'development',
  PORT: Number(process.env.PORT || 5000),
  DATABASE_URL: getEnv('DATABASE_URL'),
  JWT_SECRET: getEnv('JWT_ACCESS_SECRET'),
  JWT_EXPIRES_IN: process.env.JWT_ACCESS_EXPIRES_IN || '15m',      
  REFRESH_JWT_SECRET: getEnv('JWT_REFRESH_SECRET'),         
  REFRESH_JWT_EXPIRES_IN: process.env.JWT_REFRESH_EXPIRES_IN || '7d', 
  RESEND_API_KEY: getEnv('RESEND_API_KEY'),
  RESEND_FROM_EMAIL: getEnv('RESEND_FROM_EMAIL', 'Stack From Scratch <no-reply@artisticvickey.in>'),
};