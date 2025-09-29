// useSessionStorage.ts - SessionStorage操作Hook
import { useState, useEffect } from 'react';

export const useSessionStorage = () => {
  const getItem = (key: string): string | null => {
    try {
      return sessionStorage.getItem(key);
    } catch (error) {
      console.error('Error reading from sessionStorage:', error);
      return null;
    }
  };

  const setItem = (key: string, value: string): void => {
    try {
      sessionStorage.setItem(key, value);
    } catch (error) {
      console.error('Error writing to sessionStorage:', error);
    }
  };

  const removeItem = (key: string): void => {
    try {
      sessionStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing from sessionStorage:', error);
    }
  };

  const clear = (): void => {
    try {
      sessionStorage.clear();
    } catch (error) {
      console.error('Error clearing sessionStorage:', error);
    }
  };

  return {
    getItem,
    setItem,
    removeItem,
    clear,
  };
};