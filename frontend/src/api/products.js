import api from './axios';

export const productsAPI = {
  getProducts: async (params = {}) => {
    const response = await api.get('/products/', { params });
    return response.data;
  },

  getProduct: async (id) => {
    const response = await api.get(`/products/${id}`);
    return response.data;
  },
};