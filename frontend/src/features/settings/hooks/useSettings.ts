import { useMutation } from '@tanstack/react-query';
import { userService } from '../services/user.service';
import { useAuth } from '../../../hooks/useAuth';

export function useUpdateProfile() {
  const { refreshUser } = useAuth();

  return useMutation({
    mutationFn: ({ userId, fullName }: { userId: string; fullName: string }) =>
      userService.updateUser(userId, fullName),
    onSuccess: () => {
      refreshUser();
    },
  });
}

export function useExportData() {
  return useMutation({
    mutationFn: (userId: string) => userService.exportUserData(userId),
    onSuccess: (data) => {
      const element = document.createElement('a');
      const file = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      element.href = URL.createObjectURL(file);
      element.download = `interviewsage_data_export_${Date.now()}.json`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    },
  });
}
