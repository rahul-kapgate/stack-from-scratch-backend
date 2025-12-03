import { prisma } from '../db/prisma.js';
import { sendOtpEmail } from './emailService.js';

const OTP_EXPIRY_MINUTES = 5;

function generateOtpCode() {
  // 6-digit numeric OTP
  return String(Math.floor(100000 + Math.random() * 900000));
}

export async function createAndSendEmailOtp({
  email,
  firstName,
  payload,          
  purpose = 'VERIFY_EMAIL',
}) {
  const code = generateOtpCode();
  const expiresAt = new Date(Date.now() + OTP_EXPIRY_MINUTES * 60 * 1000);

  await prisma.emailOtp.create({
    data: {
      email,
      code,
      purpose,
      expiresAt,
      payload,
    },
  });

  await sendOtpEmail({
    email,
    firstName,
    code,
  });
}

export async function verifyEmailOtp({ email, code, purpose = 'VERIFY_EMAIL' }) {
  const now = new Date();

  const otp = await prisma.emailOtp.findFirst({
    where: {
      email,
      purpose,
      used: false,
      expiresAt: { gt: now },
    },
    orderBy: { createdAt: 'desc' },
  });

  if (!otp || otp.code !== code) {
    const error = new Error('Invalid or expired code');
    error.statusCode = 400;
    throw error;
  }

  await prisma.emailOtp.update({
    where: { id: otp.id },
    data: { used: true },
  });

  return otp; 
}
