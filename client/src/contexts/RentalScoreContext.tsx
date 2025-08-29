import { createContext, useState, useEffect, ReactNode } from "react";
import { RentalScore } from "../type";
import httpClient from "../services/httpClient";

interface RentalScoreContextType {
  rentalScores: RentalScore[];
  updateQolScores: (qolUpdates: { id: number; qolScore: number }[]) => void;
}

export const RentalScoreContext = createContext<RentalScoreContextType>({
  rentalScores: [],
  updateQolScores: () => {},
});

export const RentalScoreProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [rentalScores, setRentalScores] = useState<RentalScore[]>([]);

  useEffect(() => {
    const fetchRentalScores = async () => {
      try {
        const response = await httpClient.get<RentalScore[]>("/api/rentalScore");
        return response.data;
      } catch (error) {
        console.error("Error fetching rental scores:", error);
      }
    };
    void fetchRentalScores().then((data) => setRentalScores(data!));
  }, []);

  const updateQolScores = (qolUpdates: { id: number; qolScore: number }[]) => {
    setRentalScores(prevScores =>
      prevScores.map(score => {
        const update = qolUpdates.find(u => u.id === score.id);
        return update ? { ...score, qolScore: update.qolScore } : score;
      })
    );
  };

  const contextValue: RentalScoreContextType = {
    rentalScores,
    updateQolScores,
  };

  return (
    <RentalScoreContext.Provider value={contextValue}>
      {children}
    </RentalScoreContext.Provider>
  );
};
