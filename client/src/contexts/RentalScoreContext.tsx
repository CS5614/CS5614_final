import { createContext, useState, useEffect, ReactNode } from "react";
import { RentalScore } from "../type";
import httpClient from "../services/httpClient";

export const RentalScoreContext = createContext<RentalScore[]>([]);

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

  return (
    <RentalScoreContext.Provider value={rentalScores}>
      {children}
    </RentalScoreContext.Provider>
  );
};
