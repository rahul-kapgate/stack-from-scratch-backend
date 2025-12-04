// src/services/authService.js
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { prisma } from '../db/prisma.js';
import { ENV } from '../config/env.js';
import { createAndSendEmailOtp, verifyEmailOtp } from '../services/otpService.js';

const SALT_ROUNDS = 10;

function sanitizeUser(user) {
    if (!user) return null;
    const { passwordHash, ...safe } = user;
    return safe;
}

function generateTokens(user) {
    const accessToken = jwt.sign(
        { sub: user.id, role: user.role },
        ENV.JWT_SECRET,
        { expiresIn: ENV.JWT_EXPIRES_IN }
    );

    const refreshToken = jwt.sign(
        { sub: user.id, role: user.role },
        ENV.REFRESH_JWT_SECRET,
        { expiresIn: ENV.REFRESH_JWT_EXPIRES_IN }
    );

    return { accessToken, refreshToken };
}

function verifyRefreshToken(refreshToken) {
    try {
        return jwt.verify(refreshToken, ENV.REFRESH_JWT_SECRET);
    } catch (err) {
        const error = new Error('Invalid or expired refresh token');
        error.statusCode = 401;
        throw error;
    }
}


// small validations
function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhone(phone) {
    return /^[0-9]{7,15}$/.test(phone);
}

export async function signupUser({ firstName, lastName, email, phone, password }) {
    if (!firstName || !lastName || !email || !phone || !password) {
        const error = new Error('firstName, lastName, email, phone, password are required');
        error.statusCode = 400;
        throw error;
    }

    if (!validateEmail(email)) {
        const error = new Error('Invalid email format');
        error.statusCode = 400;
        throw error;
    }

    if (!validatePhone(phone)) {
        const error = new Error('Invalid phone number');
        error.statusCode = 400;
        throw error;
    }

    if (password.length < 8) {
        const error = new Error('Password must be at least 8 characters');
        error.statusCode = 400;
        throw error;
    }

    const existing = await prisma.user.findFirst({
        where: {
            OR: [{ email }, { phone }],
        },
    });

    if (existing) {
        const error = new Error('User with this email or phone already exists');
        error.statusCode = 409;
        throw error;
    }

    const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

    await createAndSendEmailOtp({
        email,
        firstName,
        payload: {
          firstName,
          lastName,
          email,
          phone,
          passwordHash,
        },
      });
    
      return { email };
    }


    export async function verifyEmailOtpService({ email, code }) {
        if (!email || !code) {
          const error = new Error('email and code are required');
          error.statusCode = 400;
          throw error;
        }
      
        if (!validateEmail(email)) {
          const error = new Error('Invalid email format');
          error.statusCode = 400;
          throw error;
        }
      
        // verify OTP and get stored payload
        const otp = await verifyEmailOtp({ email, code });
      
        if (!otp.payload) {
          const error = new Error('Signup data not found for this OTP');
          error.statusCode = 400;
          throw error;
        }
      
        const { firstName, lastName, phone, passwordHash } = otp.payload;
      
        // extra safety: ensure user still doesn't exist
        const existing = await prisma.user.findFirst({
          where: {
            OR: [{ email }, { phone }],
          },
        });
      
        if (existing) {
          const error = new Error('User with this email or phone already exists');
          error.statusCode = 409;
          throw error;
        }
      
        const user = await prisma.user.create({
          data: {
            firstName,
            lastName,
            email,
            phone,
            passwordHash,
            emailVerified: true,
          },
        });
      
        const { accessToken, refreshToken } = generateTokens(user);
      
        return {
          user: sanitizeUser(user),
          accessToken,
          refreshToken,
        };
      }
      

export async function loginUser({ email, password }) {
    if (!email || !password) {
        const error = new Error('email and password are required');
        error.statusCode = 400;
        throw error;
    }

    const user = await prisma.user.findUnique({
        where: { email },
    });

    if (!user) {
        const error = new Error('Invalid email or password');
        error.statusCode = 401;
        throw error;
    }

    if (!user.emailVerified) {
        const error = new Error('Please verify your email before logging in');
        error.statusCode = 403;
        throw error;
    }

    const isMatch = await bcrypt.compare(password, user.passwordHash);
    if (!isMatch) {
        const error = new Error('Invalid email or password');
        error.statusCode = 401;
        throw error;
    }

    const { accessToken, refreshToken } = generateTokens(user);
    console.log(`${user.firstName} ${user.lastName} Logged in`);
    return {
        user: sanitizeUser(user),
        accessToken,
        refreshToken,
    };
}

export async function refreshAccessTokenService({ refreshToken }) {
    if (!refreshToken) {
      const error = new Error('refreshToken is required');
      error.statusCode = 400;
      throw error;
    }
  
    const payload = verifyRefreshToken(refreshToken);
  
    const user = await prisma.user.findUnique({
      where: { id: payload.sub },
    });
  
    if (!user || !user.emailVerified) {
      const error = new Error('User not found or not verified');
      error.statusCode = 401;
      throw error;
    }
  
    const { accessToken, refreshToken: newRefreshToken } = generateTokens(user);
  
    return {
      user: sanitizeUser(user),
      accessToken,
      refreshToken: newRefreshToken,
    };
  }
  

