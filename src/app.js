import express from "express";
import { ENV } from "./config/env.js";
import cors from 'cors';
import cookieParser from 'cookie-parser';
import { errorHandler } from "./middlewares/errorHandler.js";
import authRoutes from './routes/auth.routes.js';

const app = express();

// Middlewares
app.use(express.json());
app.use((req, res, next) => {
  console.log("Request Origin:", req.headers.origin);
  next();
});

app.use(
  cors({
    origin: ['http://localhost:3000',
      'https://stack-from-scratch.netlify.app'],
    credentials: true,
  })
);
app.use(express.json());
app.use(cookieParser());

// Health check 
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    env: ENV.NODE_ENV,
  });
});

// API routes
app.use('/api/auth', authRoutes);

//Error handler 
app.use(errorHandler);

export default app;
