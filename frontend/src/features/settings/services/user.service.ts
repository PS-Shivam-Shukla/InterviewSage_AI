import { apiClient } from '../../../api/client';
import { UserProfile } from '../../../types/auth.types';

export const userService = {
  async updateUser(userId: string, fullName: string): Promise<UserProfile> {
    const response = await apiClient.patch<UserProfile>(`/users/${userId}`, {
      full_name: fullName,
    });
    return response.data;
  },

  async exportUserData(userId: string): Promise<Record<string, any>> {
    const response = await apiClient.get<Record<string, any>>(`/users/${userId}/export`);
    return response.data;
  },
};
