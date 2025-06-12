export function getCSRFToken() {
  const cookieName = "csrftoken";
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(cookieName + "=")) {
      return decodeURIComponent(cookie.substring(cookieName.length + 1));
    }
  }
  const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
  return csrfInput ? csrfInput.value : null;
}
