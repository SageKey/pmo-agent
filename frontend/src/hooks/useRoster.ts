import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PersonDemand, TeamMember } from "@/types/roster";

export function useRoster() {
  return useQuery({
    queryKey: ["roster"],
    queryFn: async () => {
      const { data } = await api.get<TeamMember[]>("/roster/");
      return data;
    },
  });
}

export function usePersonDemand() {
  return useQuery({
    queryKey: ["roster", "demand"],
    queryFn: async () => {
      const { data } = await api.get<PersonDemand[]>("/roster/demand");
      return data;
    },
  });
}
