/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React, { useState } from 'react';
import './App.css';
import LandingScreen from './components/LandingScreen';
import CategoryScreen from './components/CategoryScreen';
import InputScreen from './components/InputScreen';
import ResultsScreen from './components/ResultsScreen';

function App() {
  const [currentScreen, setCurrentScreen] = useState('landing');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [userState, setUserState] = useState('California');
  const [results, setResults] = useState(null);

  const handleGetHelp = () => {
    setCurrentScreen('category');
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    setCurrentScreen('input');
  };

  const handleSubmitInput = async (input, state, photos) => {
    setUserState(state);
    setCurrentScreen('results');

    // Call the backend API
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/guard`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category: selectedCategory,
          state: state,
          rant: input
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data);
      } else {
        setResults({
          error: "Something went wrong — try again"
        });
      }
    } catch (error) {
      setResults({
        error: "Something went wrong — try again"
      });
    }
  };

  const handleStartNew = () => {
    setCurrentScreen('landing');
    setSelectedCategory('');
    setResults(null);
  };

  const renderScreen = () => {
    switch (currentScreen) {
      case 'landing':
        return <LandingScreen onGetHelp={handleGetHelp} />;
      case 'category':
        return <CategoryScreen onSelectCategory={handleCategorySelect} />;
      case 'input':
        return <InputScreen
          category={selectedCategory}
          onSubmit={handleSubmitInput}
          defaultState={userState}
        />;
      case 'results':
        return <ResultsScreen
          results={results}
          onStartNew={handleStartNew}
        />;
      default:
        return <LandingScreen onGetHelp={handleGetHelp} />;
    }
  };

  return (
    <div className="App">
      {renderScreen()}
    </div>
  );
}

export default App;
