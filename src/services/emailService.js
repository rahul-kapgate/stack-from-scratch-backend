// src/services/emailService.js
import { Resend } from 'resend';
import { ENV } from '../config/env.js';

const resend = new Resend(ENV.RESEND_API_KEY);

export async function sendOtpEmail({ email, firstName, code }) {
  const html = `
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>Verification Code - Stack From Scratch</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body style="margin:0; padding:0; background-color:#f4f4f7; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f4f4f7; padding:24px 0;">
          <tr>
            <td align="center">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="max-width:520px; background-color:#ffffff; border-radius:16px; box-shadow:0 10px 30px rgba(15,23,42,0.10); overflow:hidden;">
                <!-- Header -->
                <tr>
                  <td style="padding:20px 24px; background:linear-gradient(135deg,#0f172a,#1d4ed8); color:#e5e7eb;">
                    <div style="font-size:14px; letter-spacing:0.08em; text-transform:uppercase; opacity:0.85;">
                      Stack From Scratch
                    </div>
                    <div style="margin-top:6px; font-size:20px; font-weight:600; color:#f9fafb;">
                      Email Verification Code
                    </div>
                  </td>
                </tr>

                <!-- Content -->
                <tr>
                  <td style="padding:24px 24px 8px 24px; color:#0f172a;">
                    <p style="margin:0 0 10px 0; font-size:15px;">
                      Hi <strong>${firstName || 'there'}</strong>,
                    </p>
                    <p style="margin:0 0 16px 0; font-size:14px; line-height:1.6; color:#4b5563;">
                      Use the verification code below to complete your sign up to
                      <strong>Stack From Scratch</strong>.
                    </p>

                    <!-- OTP Code -->
                    <div style="margin:18px 0; text-align:center;">
                      <div
                        style="
                          display:inline-block;
                          padding:14px 24px;
                          border-radius:999px;
                          background:rgba(37,99,235,0.06);
                          border:1px solid rgba(37,99,235,0.35);
                        "
                      >
                        <span style="font-size:24px; font-weight:700; letter-spacing:0.35em; color:#1d4ed8;">
                          ${code}
                        </span>
                      </div>
                    </div>

                    <p style="margin:0 0 10px 0; font-size:13px; line-height:1.6; color:#6b7280; text-align:center;">
                      This code will expire in <strong>5 minutes</strong>.
                    </p>

                    <p style="margin:18px 0 0 0; font-size:13px; line-height:1.6; color:#6b7280;">
                      If you didn’t request this, you can safely ignore this email.
                    </p>
                  </td>
                </tr>

                <!-- Footer -->
                <tr>
                  <td style="padding:16px 24px 20px 24px; border-top:1px solid #e5e7eb; background-color:#f9fafb;">
                    <p style="margin:0; font-size:12px; color:#9ca3af; line-height:1.5;">
                      Thanks,<br />
                      <span style="color:#4b5563;">Stack From Scratch Team</span>
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
  `;

  // optional plain-text fallback
  const text = `Hi ${firstName || 'there'},

Your verification code is: ${code}

This code will expire in 5 minutes.

If you didn’t request this, you can ignore this email.
– Stack From Scratch Team`;

  const { data, error } = await resend.emails.send({
    from: ENV.RESEND_FROM_EMAIL,
    to: email,
    subject: 'Verification Code - Stack From Scratch',
    html,
    text,
  });

  if (error) {
    console.error('Resend OTP email error:', error);
    const err = new Error('Failed to send OTP email');
    err.statusCode = 502;
    throw err;
  }

  console.log('Resend OTP email sent:', data?.id || data);
  return data;
}
