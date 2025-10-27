import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Trash2, Plus, Minus, ShoppingBag, Loader2 } from 'lucide-react';
import { useCartStore } from '../store/cartStore';

export default function Cart() {
  const { cart, isLoading, fetchCart, updateQuantity, removeFromCart } = useCartStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCart();
  }, []);

  const formatPrice = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
    }).format(price);
  };

  const handleUpdateQuantity = async (itemId, currentQuantity, change) => {
    const newQuantity = currentQuantity + change;
    if (newQuantity > 0) {
      await updateQuantity(itemId, newQuantity);
    }
  };

  const handleCheckout = () => {
    navigate('/checkout');
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        </div>
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-20">
          <ShoppingBag className="mx-auto h-16 w-16 text-gray-400" />
          <h2 className="mt-4 text-2xl font-bold text-gray-900">
            Tu carrito está vacío
          </h2>
          <p className="mt-2 text-gray-600">
            Agrega productos para comenzar tu compra
          </p>
          <Link
            to="/products"
            className="mt-6 inline-block btn-primary"
          >
            Ver productos
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Carrito de Compras
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {cart.items.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-lg shadow-md p-6 flex items-center space-x-4"
            >
              {/* Product Image */}
              <div className="h-24 w-24 bg-gray-200 rounded-lg flex-shrink-0 overflow-hidden">
                {item.product_image_url ? (
                  <img
                    src={item.product_image_url}
                    alt={item.product_name}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="h-full w-full flex items-center justify-center text-gray-400 text-xs">
                    Sin imagen
                  </div>
                )}
              </div>

              {/* Product Info */}
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">
                  {item.product_name}
                </h3>
                <p className="text-gray-600">
                  {formatPrice(item.product_price)} c/u
                </p>

                {/* Quantity Controls */}
                <div className="mt-2 flex items-center space-x-2">
                  <button
                    onClick={() => handleUpdateQuantity(item.id, item.quantity, -1)}
                    className="p-1 rounded-md hover:bg-gray-100"
                    disabled={item.quantity <= 1}
                  >
                    <Minus className="h-4 w-4" />
                  </button>

                  <span className="px-4 py-1 bg-gray-100 rounded-md font-medium">
                    {item.quantity}
                  </span>

                  <button
                    onClick={() => handleUpdateQuantity(item.id, item.quantity, 1)}
                    className="p-1 rounded-md hover:bg-gray-100"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Subtotal and Remove */}
              <div className="text-right">
                <p className="text-xl font-bold text-primary-600">
                  {formatPrice(item.subtotal)}
                </p>
                <button
                  onClick={() => removeFromCart(item.id)}
                  className="mt-2 text-red-600 hover:text-red-700 flex items-center space-x-1"
                >
                  <Trash2 className="h-4 w-4" />
                  <span className="text-sm">Eliminar</span>
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Resumen del Pedido
            </h2>

            <div className="space-y-3">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal</span>
                <span>{formatPrice(cart.subtotal)}</span>
              </div>

              <div className="flex justify-between text-gray-600">
                <span>IVA (19%)</span>
                <span>{formatPrice(cart.tax)}</span>
              </div>

              <div className="border-t pt-3">
                <div className="flex justify-between text-xl font-bold text-gray-900">
                  <span>Total</span>
                  <span className="text-primary-600">
                    {formatPrice(cart.total)}
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={handleCheckout}
              className="mt-6 w-full btn-primary text-lg"
            >
              Proceder al Pago
            </button>

            <Link
              to="/products"
              className="mt-4 block text-center text-primary-600 hover:text-primary-700"
            >
              Seguir comprando
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}