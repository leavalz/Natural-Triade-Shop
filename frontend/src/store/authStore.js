import { create } from 'zustand';
import api from '../api/axios';
import toast from 'react-hot-toast';

export const useAuthStore = create((set, get) => ({
  user: JSON.parse(localStorage.getItem('user')) || null,
  token: localStorage.getItem('token') || null,
  isLoading: false,

  login: async (credentials) => {
    set({ isLoading: true });
    try {
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);

      const userResponse = await api.get('/auth/me');
      const user = userResponse.data;
      
      localStorage.setItem('user', JSON.stringify(user));
      set({ user, token: access_token });
      
      toast.success('Inicio de sesión exitoso');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al iniciar sesión');
      return false;
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (userData) => {
    set({ isLoading: true });
    try {
      await api.post('/auth/register', userData);
      toast.success('Registro exitoso');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al registrarse');
      return false;
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({ user: null, token: null });
    toast.success('Sesión cerrada');
  },

  isAdmin: () => {
    const { user } = get();
    return user?.role === 'admin';
  },
}));