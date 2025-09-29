import React, { createContext, useEffect } from 'react';
import { DefaultService } from '../services/api_gen/services/DefaultService';

// 默认值类型声明
interface AuthContextType {
  user: { id: number; username: string; email: string } | null;
  token: string | null;
  loading: boolean;
  login: () => Promise<boolean>;
  logout: () => void;
  register: () => Promise<boolean>;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  loading: false,
  login: async () => true,
  logout: () => {},
  register: async () => true,
});

type AuthProviderProps = { children: React.ReactNode };

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
  const mockLogin = async () => true;
  const mockLogout = () => {};
  const mockRegister = async () => true;

  useEffect(() => {
    const ensureMockProfile = async () => {
      try {
        await DefaultService.getUserProfileApiV1UserIdGet(mockUser.id);
      } catch {
        await DefaultService.createUserProfileApiV1Post({
          user_id: mockUser.id,
          user_cv_text: 'Mock CV: JavaScript, Python, SQL',
          user_preferences_text: 'Remote, Backend',
          user_email: mockUser.email,
        });
      }
    };
    ensureMockProfile();
  }, []);

  return (
    <AuthContext.Provider value={{
      user: mockUser,
      token: 'mock-token',
      loading: false,
      login: mockLogin,
      logout: mockLogout,
      register: mockRegister,
    }}>
      {children}
    </AuthContext.Provider>
  );
};