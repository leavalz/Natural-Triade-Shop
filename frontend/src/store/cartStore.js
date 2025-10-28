import { create } from 'zustand';
import api from '../api/axios';
import toast from 'react-hot-toast';

export const useCartStore = create((set, get) => ({
  cart: null,
  isLoading: false,

  fetchCart: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get('/cart/');
      set({ cart: response.data });
    } catch (error) {
      console.error('Error fetching cart:', error);
    } finally {
      set({ isLoading: false });
    }
  },

  addToCart: async (productId, quantity) => {
    try {
      await api.post('/cart/items', {
        product_id: productId,
        quantity,
      });
      toast.success('Producto agregado al carrito');
      await get().fetchCart();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al agregar al carrito');
    }
  },

  updateQuantity: async (itemId, quantity) => {
    try {
      await api.put(`/cart/items/${itemId}`, { quantity });
      await get().fetchCart();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al actualizar cantidad');
    }
  },

  removeFromCart: async (itemId) => {
    try {
      await api.delete(`/cart/items/${itemId}`);
      toast.success('Producto eliminado');
      await get().fetchCart();
    } catch (error) {
      toast.error('Error al eliminar producto');
    }
  },

  clearCart: async () => {
    try {
      await api.delete('/cart/');
      set({ cart: null });
      toast.success('Carrito vaciado');
    } catch (error) {
      toast.error('Error al vaciar carrito');
    }
  },

  getTotalItems: () => {
    const { cart } = get();
    return cart?.items_count || 0;
  },
}));