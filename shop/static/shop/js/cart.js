;(function(){
  var cartCache = null;
  function loadCart(){
    if(cartCache) return cartCache;
    try{
      cartCache = JSON.parse(localStorage.getItem('cart')) || {};
    }catch(e){
      cartCache = {};
    }
    return cartCache;
  }
  function saveCart(){
    localStorage.setItem('cart', JSON.stringify(cartCache || {}));
  }
  window.addToCart = function(productId, name, price, quantity, size, color){
    var c = loadCart();
    var q = parseInt(quantity == null ? 1 : quantity, 10) || 1;
    var p = parseInt(price, 10) || 0;
    var s = size || 'M';
    var col = color || 'red';
    var key = 'pr' + productId + '_' + s + '_' + col;
    if(c[key]){
      c[key][0] += q;
    }else{
      c[key] = [q, name, p, s, col];
    }
    cartCache = c;
    saveCart();
    updateCartCount();
  };
  window.updateCartCount = function(){
    var c = loadCart();
    var total = 0;
    for(var k in c){
      var v = c[k];
      if(Array.isArray(v) && v.length > 0){
        total += Number(v[0]) || 0;
      }
    }
    var el = document.getElementById('cart');
    if(el){
      el.textContent = total;
    }
  };
  window.getCart = function(){ return loadCart(); };
  window.clearCart = function(){ cartCache = {}; saveCart(); updateCartCount(); };
  document.addEventListener('DOMContentLoaded', function(){ loadCart(); updateCartCount(); });
})();
