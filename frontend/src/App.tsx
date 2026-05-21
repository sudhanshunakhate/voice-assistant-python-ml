import { BrowserRouter, Routes, Route } from "react-router-dom";
import { MusicPlayerProvider } from "./context/MusicPlayerContext";
import { Layout } from "./components/Layout";
import { CommandCenter } from "./pages/CommandCenter";
import { Voice } from "./pages/Voice";
import { Music } from "./pages/Music";
import { Skills } from "./pages/Skills";
import { Settings } from "./pages/Settings";
import { History } from "./pages/History";
import { Reminders } from "./pages/Reminders";
import { Search } from "./pages/Search";

export default function App() {
  return (
    <MusicPlayerProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<CommandCenter />} />
            <Route path="/voice" element={<Voice />} />
            <Route path="/music" element={<Music />} />
            <Route path="/skills" element={<Skills />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/history" element={<History />} />
            <Route path="/reminders" element={<Reminders />} />
            <Route path="/search" element={<Search />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </MusicPlayerProvider>
  );
}
