import React, {createContext, useContext} from 'react';

export interface Layout {
  width: number;
  height: number;
  isPortrait: boolean;
  scale: number;
  pad: number;
}

const LayoutContext = createContext<Layout>({
  width: 1920,
  height: 1080,
  isPortrait: false,
  scale: 1,
  pad: 90,
});

export const useLayout = () => useContext(LayoutContext);

export const LayoutProvider: React.FC<{
  width: number;
  height: number;
  children: React.ReactNode;
}> = ({width, height, children}) => {
  const isPortrait = height > width;
  const scale = isPortrait ? width / 1400 : width / 1920;
  const value: Layout = {
    width,
    height,
    isPortrait,
    scale,
    pad: isPortrait ? 60 : 90,
  };
  return (
    <LayoutContext.Provider value={value}>{children}</LayoutContext.Provider>
  );
};
