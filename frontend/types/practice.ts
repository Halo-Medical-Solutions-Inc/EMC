export interface Team {
  id: string;
  title: string;
  description: string;
  members: string[];
}

export interface TeamsConfig {
  teams: Team[];
}

export interface TeamCreate {
  title: string;
  description: string;
}

export interface TeamUpdate {
  title: string;
  description: string;
}

export interface TeamMembersUpdate {
  members: string[];
}

export interface Practice {
  id: string;
  practice_name: string;
  practice_region: string;
  active_call_ids: string[];
  max_concurrent_calls: number;
  teams: TeamsConfig;
  created_at: string;
  updated_at: string;
}

export interface PracticeUpdate {
  practice_name?: string;
  practice_region?: string;
}
