import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from './pages/home';
import Detect from './pages/detect';
import DetectReport from './pages/detect/Report';
import About from './pages/about';
import Nav from "./components/Nav";
import Footer from "./components/Footer";
import MobileBottomNav from "./components/MobileBottomNav";
import ScrollToTop from "./components/ScrollToTop";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Contact from "./pages/contact";

function App() {

  return (
    <div className="font-futura text-black min-h-[100dvh]">
      <ToastContainer className="!top-[max(1rem,env(safe-area-inset-top))] max-lg:!mb-[5.25rem] max-lg:!px-2" />
      <BrowserRouter>
        <ScrollToTop />
        <Nav />
        <main
          className="lg:pb-0 pb-[calc(4.5rem+env(safe-area-inset-bottom,0px))] max-w-[100vw] overflow-x-hidden"
        >
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/index.html" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/detect" element={<Detect />} />
            <Route path="/detect/report" element={<DetectReport />} />
            <Route path="/contact" element={<Contact />} />
          </Routes>
        </main>
        <Footer />
        <MobileBottomNav />
      </BrowserRouter>
    </div>
  )
}

export default App
