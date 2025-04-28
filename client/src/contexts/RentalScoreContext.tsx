import { createContext, useState, useEffect, ReactNode } from "react";
import { RentalScore } from "../type";
import axios from "axios";

export const RentalScoreContext = createContext<RentalScore[]>([]);

export const RentalScoreProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [rentalScores, setRentalScores] = useState<RentalScore[]>([]);

  useEffect(() => {
    const fetchRentalScores = async () => {
      try {
        const response = await axios.get("http://0.0.0.0:8000/api/rentalScore");
        const data = response.data;
        const rentalScores = data as RentalScore[];
        // console.log(
        //   rentalScores.filter(
        //     (f) => f.long === -77.230797 && f.lat === 38.87051
        //   )
        // ); // Log the first 5 rental scores
        return rentalScores;
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
