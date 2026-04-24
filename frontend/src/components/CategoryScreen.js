/*
 * The Guard Table — The Good Neighbor Guard
 * Built by Christopher Hughes · Sacramento, CA
 * Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
 * Truth · Safety · We Got Your Back
 */

import React from 'react';

const CategoryScreen = ({ onSelectCategory }) => {
  const categories = [
    {
      id: 'housing',
      icon: '🏠',
      title: 'My Housing',
      description: 'Eviction, landlord won\'t fix it, deposit stolen, unsafe conditions, illegal entry'
    },
    {
      id: 'money',
      icon: '💵',
      title: 'They\'re Coming After My Money',
      description: 'Debt collectors, bank fees, repossession, payday loans, utility shutoff'
    },
    {
      id: 'job',
      icon: '💼',
      title: 'My Job is Cheating Me',
      description: 'Missing pay, PTO shorted, last check not paid, fired without cause, overtime denied, harassment ignored'
    },
    {
      id: 'benefits',
      icon: '🏥',
      title: 'My Benefits or Insurance',
      description: 'Medicaid cut, food stamps terminated, unemployment denied, insurance claim denied, hospital bill wrong'
    },
    {
      id: 'family',
      icon: '👨‍👩‍👧',
      title: 'My Family',
      description: 'School ignoring my kid, contractor took my money, someone scammed someone I love'
    },
    {
      id: 'other',
      icon: '⚡',
      title: 'Something Else',
      description: 'Anything not listed above — describe it and we\'ll figure it out'
    }
  ];

  return (
    <div className="category-screen">
      <div className="category-header">
        <h1>What are they doing to you?</h1>
      </div>
      <div className="category-grid">
        {categories.map((category) => (
          <div
            key={category.id}
            className="category-card"
            onClick={() => onSelectCategory(category.id)}
          >
            <div className="category-card-icon">{category.icon}</div>
            <div className="category-card-title">{category.title}</div>
            <div className="category-card-desc">{category.description}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CategoryScreen;