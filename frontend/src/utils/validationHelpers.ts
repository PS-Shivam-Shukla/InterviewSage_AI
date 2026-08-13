import { z } from 'zod';

export const emailSchema = z.string().email('Please enter a valid email address');
export const passwordSchema = z.string().min(8, 'Password must be at least 8 characters long');

export const loginSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
});

export const registerSchema = z.object({
  full_name: z.string().min(2, 'Full name is required'),
  email: emailSchema,
  password: passwordSchema,
  role: z.enum(['CANDIDATE', 'RECRUITER', 'ADMIN']).default('CANDIDATE'),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
