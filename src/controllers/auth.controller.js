import {
  signupUser,
  loginUser,
  verifyEmailOtpService,
  refreshAccessTokenService,
} from '../services/authService.js';


export async function signup(req, res, next) {
  try {
    const { firstName, lastName, email, phone, password } = req.body;

    await signupUser({
      firstName,
      lastName,
      email,
      phone,
      password,
    });

    return res.status(200).json({
      message: 'OTP sent to your email. Please verify to complete signup.',
      email,
    });
  } catch (err) {
    next(err);
  }
}

export async function verifyEmail(req, res, next) {
  try {
    const { email, code } = req.body;

    const { user, accessToken, refreshToken } =
      await verifyEmailOtpService({ email, code });

    return res.status(200).json({
      message: 'Email verified successfully',
      user,
      accessToken,
      refreshToken,
    });
  } catch (err) {
    next(err);
  }
}

export async function login(req, res, next) {
  try {
    const { email, password } = req.body;

    const { user, accessToken, refreshToken } = await loginUser({
      email,
      password,
    });

    return res.status(200).json({
      message: 'Login successful',
      user,
      accessToken,
      refreshToken,
    });
  } catch (err) {
    next(err);
  }
}


export async function refreshToken(req, res, next) {
  try {
    const { refreshToken } = req.body;

    const { user, accessToken, refreshToken: newRefreshToken } =
      await refreshAccessTokenService({ refreshToken });

    return res.status(200).json({
      message: 'Token refreshed',
      user,
      accessToken,
      refreshToken: newRefreshToken,
    });
  } catch (err) {
    next(err);
  }
}
