// Configuración de Firebase para el proyecto "mi-cartera".
// Estas claves NO son secretas — Firebase está diseñado para que vivan en el
// navegador. La seguridad de verdad la ponen las reglas de Firestore
// (archivo firestore.rules), no el hecho de ocultar esto.
 
const firebaseConfig = {
  apiKey: "AIzaSyBFLIzZBPi5IkhFwBxD_cAC5WRg6Abh-Z0",
  authDomain: "mi-cartera-a289a.firebaseapp.com",
  projectId: "mi-cartera-a289a",
  storageBucket: "mi-cartera-a289a.firebasestorage.app",
  messagingSenderId: "420701269832",
  appId: "1:420701269832:web:8828b2b6f444a04a598d7d"
};
 
firebase.initializeApp(firebaseConfig);
