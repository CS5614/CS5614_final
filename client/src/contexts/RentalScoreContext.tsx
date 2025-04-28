import { createContext, useState, useEffect, ReactNode } from "react";
import { RentalScore } from "../type";

export const RentalScoreContext = createContext<RentalScore[]>([]);

export const RentalScoreProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [rentalScores, setRentalScores] = useState<RentalScore[]>([]);

  useEffect(() => {
    const fetchRentalScores = async () => {
      try {
        const response = await fetch("http://0.0.0.0:8000/api/rentalScore");
        console.log("fetch");
        if (!response.ok) {
          throw new Error("Failed to fetch rental scores");
        }
        const data = await response.json();
        setRentalScores(data as RentalScore[]);
      } catch (error) {
        console.error("Error fetching rental scores:", error);
      }
    };
    fetchRentalScores();
  }, []);

  return (
    <RentalScoreContext.Provider value={rentalScores}>
      {children}
    </RentalScoreContext.Provider>
  );
};
