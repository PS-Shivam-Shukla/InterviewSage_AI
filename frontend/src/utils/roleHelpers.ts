import { UserRole } from '../types/auth.types';

/**
 * Role checking helper functions.
 */
export function isAdmin(role?: UserRole): boolean {
  return role === 'ADMIN';
}

export function isRecruiter(role?: UserRole): boolean {
  return role === 'RECRUITER' || role === 'ADMIN';
}

export function isCandidate(role?: UserRole): boolean {
  return role === 'CANDIDATE' || role === 'ADMIN';
}

export function hasAnyRole(userRole?: UserRole, allowedRoles?: UserRole[]): boolean {
  if (!allowedRoles || allowedRoles.length === 0) return true;
  if (!userRole) return false;
  return allowedRoles.includes(userRole) || userRole === 'ADMIN';
}
