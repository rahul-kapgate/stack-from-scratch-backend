import jwt from 'jsonwebtoken';

export function authRequired(req, res, next) {
  try {

    const token =
      req.cookies?.access_token ||
      (req.headers.authorization || '').replace('Bearer ', '');

    if (!token) {
      return res.status(401).json({ message: 'Not authenticated' });
    }

    const payload = jwt.verify(token, process.env.JWT_ACCESS_SECRET);

    req.user = {
      id: payload.userId,
    };

    next();
  } catch (err) {
    console.error('Auth error:', err.message);
    return res.status(401).json({ message: 'Invalid or expired token' });
  }
}
