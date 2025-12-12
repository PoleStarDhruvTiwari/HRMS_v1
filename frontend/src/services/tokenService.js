// services/tokenService.js
class TokenService {
  getAccessToken() {
    return localStorage.getItem("access_token");
  }

  setAccessToken(token) {
    localStorage.setItem("access_token", token);
  }

  clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
  }

  getUser() {
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
  }
}

export default new TokenService();