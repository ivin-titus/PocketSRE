import "./styles.css";

const app = document.querySelector("#app");
const token = new URLSearchParams(window.location.search).get("token");

if (!token) {
  app.innerHTML = "<h1>PocketSRE</h1><p>A signed incident link is required.</p>";
}
