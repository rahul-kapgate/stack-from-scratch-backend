// src/routes/authRoutes.js
import { Router } from 'express';
import {
  signup,
  login,
  verifyEmail,
  refreshToken,
} from '../controllers/auth.controller.js';

const router = Router();

router.post('/signup', signup);
router.post('/verify-email', verifyEmail);
router.post('/login', login);
router.post('/refresh-token', refreshToken); 

export default router;
