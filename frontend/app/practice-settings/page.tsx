"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Edit, MoreVertical, Plus, Trash2, X } from "lucide-react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { useAppDispatch, useAppSelector } from "@/store";
import {
  addTeam,
  deleteTeam,
  fetchPractice,
  updatePractice,
  updateTeam,
  updateTeamMembers,
} from "@/store/slices/practice-slice";
import { PracticeUpdate, Team } from "@/types/practice";
import { User as UserType } from "@/types/user";

interface TeamCardProps {
  team: Team;
  users: UserType[];
  onEdit: () => void;
  onDelete: () => void;
  onAddMember: (userId: string) => void;
  onRemoveMember: (userId: string) => void;
}

function TeamCard({
  team,
  users,
  onEdit,
  onDelete,
  onAddMember,
  onRemoveMember,
}: TeamCardProps) {
  const [addPopoverOpen, setAddPopoverOpen] = useState(false);
  const teamMembers = users.filter((u) => team.members.includes(u.id));
  const availableUsers = users.filter((u) => !team.members.includes(u.id));

  function handleAddMember(userId: string) {
    onAddMember(userId);
    setAddPopoverOpen(false);
  }

  return (
    <div
      className="rounded-lg border border-neutral-100"
      style={{ backgroundColor: "#FDFDFD" }}
    >
      <div className="flex items-center justify-between border-b border-neutral-100 px-4 py-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-[14px] font-medium text-neutral-900">{team.title}</h3>
          {team.description && (
            <p className="mt-0.5 truncate text-[12px] text-neutral-500">{team.description}</p>
          )}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
              <MoreVertical className="h-4 w-4 text-neutral-500" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-auto">
            <DropdownMenuItem onClick={onEdit}>
              <Edit className="mr-2 h-4 w-4" />
              <span>Edit</span>
            </DropdownMenuItem>
            <DropdownMenuItem variant="destructive" onClick={onDelete}>
              <Trash2 className="mr-2 h-4 w-4" />
              <span>Delete</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="p-3">
        <div className="space-y-2">
          {teamMembers.map((member) => (
            <div
              key={member.id}
              className="group flex items-center justify-between rounded-md border border-neutral-100 bg-white px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-medium text-neutral-900">
                  {member.full_name}
                </p>
                <p className="truncate text-[11px] text-neutral-500">{member.email}</p>
              </div>
              <button
                onClick={() => onRemoveMember(member.id)}
                className="ml-2 rounded p-1 opacity-0 transition-opacity hover:bg-neutral-100 group-hover:opacity-100"
              >
                <X className="h-3.5 w-3.5 text-neutral-400" />
              </button>
            </div>
          ))}

          <Popover open={addPopoverOpen} onOpenChange={setAddPopoverOpen}>
            <PopoverTrigger asChild>
              <button className="flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed border-neutral-200 py-2 text-[13px] text-neutral-500 transition-colors hover:border-neutral-300 hover:bg-neutral-50 hover:text-neutral-600">
                <Plus className="h-3.5 w-3.5" />
                Add Member
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-0" align="start">
              <Command>
                <CommandInput placeholder="Search team members..." className="h-9" />
                <CommandList>
                  <CommandEmpty>No staff found.</CommandEmpty>
                  <CommandGroup>
                    {availableUsers.map((user) => (
                      <CommandItem
                        key={user.id}
                        value={`${user.full_name} ${user.email}`}
                        onSelect={() => handleAddMember(user.id)}
                        className="cursor-pointer"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-[13px] font-medium text-neutral-900">
                            {user.full_name}
                          </p>
                          <p className="truncate text-[11px] text-neutral-500">{user.email}</p>
                        </div>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        </div>
      </div>
    </div>
  );
}

export default function PracticeSettingsPage() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { practice, loading } = useAppSelector((state) => state.practice);
  const { user } = useAppSelector((state) => state.auth);
  const { users } = useAppSelector((state) => state.users);

  const [activeTab, setActiveTab] = useState<"teams" | "general">("teams");
  const [practiceName, setPracticeName] = useState("");
  const [practiceRegion, setPracticeRegion] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);

  const [addTeamDialogOpen, setAddTeamDialogOpen] = useState(false);
  const [editTeamDialogOpen, setEditTeamDialogOpen] = useState(false);
  const [deleteTeamDialogOpen, setDeleteTeamDialogOpen] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [newTeamTitle, setNewTeamTitle] = useState("");
  const [newTeamDescription, setNewTeamDescription] = useState("");
  const [editTeamTitle, setEditTeamTitle] = useState("");
  const [editTeamDescription, setEditTeamDescription] = useState("");
  const [loadingAction, setLoadingAction] = useState(false);

  const [localTeams, setLocalTeams] = useState<Team[]>([]);


  useEffect(() => {
    dispatch(fetchPractice());
  }, [dispatch]);

  useEffect(() => {
    if (practice) {
      setPracticeName(practice.practice_name);
      setPracticeRegion(practice.practice_region || "");
    }
  }, [practice]);

  useEffect(() => {
    if (practice?.teams?.teams) {
      setLocalTeams(practice.teams.teams);
    }
  }, [practice?.teams?.teams]);

  const teams = localTeams;

  async function handleAddMember(teamId: string, userId: string) {
    const team = teams.find((t) => t.id === teamId);
    if (!team) return;

    const previousTeams = [...localTeams];
    const newMembers = [...team.members, userId];

    setLocalTeams((prev) =>
      prev.map((t) => (t.id === teamId ? { ...t, members: newMembers } : t))
    );

    try {
      await dispatch(updateTeamMembers({ teamId, data: { members: newMembers } })).unwrap();
    } catch (error) {
      setLocalTeams(previousTeams);
      toast.error((error as string) || "Failed to add team member");
    }
  }

  async function handleRemoveMember(teamId: string, userId: string) {
    const team = teams.find((t) => t.id === teamId);
    if (!team) return;

    const previousTeams = [...localTeams];
    const newMembers = team.members.filter((id) => id !== userId);

    setLocalTeams((prev) =>
      prev.map((t) => (t.id === teamId ? { ...t, members: newMembers } : t))
    );

    try {
      await dispatch(updateTeamMembers({ teamId, data: { members: newMembers } })).unwrap();
    } catch (error) {
      setLocalTeams(previousTeams);
      toast.error((error as string) || "Failed to remove team member");
    }
  }

  async function handleUpdatePractice(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    if (!practiceName.trim()) {
      toast.error("Practice name cannot be empty");
      return;
    }
    setIsUpdating(true);
    try {
      const data: PracticeUpdate = {
        practice_name: practiceName,
        practice_region: practiceRegion,
      };
      await dispatch(updatePractice(data)).unwrap();
      toast.success("Practice updated successfully");
    } catch (error) {
      toast.error((error as string) || "Failed to update practice");
    } finally {
      setIsUpdating(false);
    }
  }

  async function handleAddTeam(): Promise<void> {
    if (!newTeamTitle.trim()) {
      toast.error("Team title cannot be empty");
      return;
    }
    setLoadingAction(true);
    try {
      await dispatch(addTeam({ title: newTeamTitle, description: newTeamDescription })).unwrap();
      toast.success("Team added successfully");
      setAddTeamDialogOpen(false);
      setNewTeamTitle("");
      setNewTeamDescription("");
    } catch (error) {
      toast.error((error as string) || "Failed to add team");
    } finally {
      setLoadingAction(false);
    }
  }

  async function handleEditTeam(): Promise<void> {
    if (!selectedTeam || !editTeamTitle.trim()) {
      toast.error("Team title cannot be empty");
      return;
    }
    setLoadingAction(true);
    try {
      await dispatch(
        updateTeam({
          teamId: selectedTeam.id,
          data: { title: editTeamTitle, description: editTeamDescription },
        })
      ).unwrap();
      toast.success("Team updated successfully");
      setEditTeamDialogOpen(false);
      setSelectedTeam(null);
      setEditTeamTitle("");
      setEditTeamDescription("");
    } catch (error) {
      toast.error((error as string) || "Failed to update team");
    } finally {
      setLoadingAction(false);
    }
  }

  async function handleDeleteTeam(): Promise<void> {
    if (!selectedTeam) return;
    setLoadingAction(true);
    try {
      await dispatch(deleteTeam(selectedTeam.id)).unwrap();
      toast.success("Team deleted successfully");
      setDeleteTeamDialogOpen(false);
      setSelectedTeam(null);
    } catch (error) {
      toast.error((error as string) || "Failed to delete team");
    } finally {
      setLoadingAction(false);
    }
  }

  function openEditDialog(team: Team): void {
    setSelectedTeam(team);
    setEditTeamTitle(team.title);
    setEditTeamDescription(team.description);
    setEditTeamDialogOpen(true);
  }

  function openDeleteDialog(team: Team): void {
    setSelectedTeam(team);
    setDeleteTeamDialogOpen(true);
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (loading && !practice) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <>
      <header className="border-b border-neutral-100 bg-white">
        <div className="px-10 py-8">
          <div className="mb-6">
            <h1 className="text-[24px] font-semibold tracking-tight text-neutral-900">
              Practice Settings
            </h1>
            <p className="mt-1 text-[15px] text-neutral-500">
              Manage practice details and team assignments.
            </p>
          </div>
        </div>

        <div className="px-10">
          <div className="flex gap-6 border-b border-neutral-100">
            <button
              onClick={() => setActiveTab("teams")}
              className={`relative pb-3 text-[14px] font-medium transition-colors whitespace-nowrap ${
                activeTab === "teams"
                  ? "text-neutral-900"
                  : "text-neutral-500 hover:text-neutral-700"
              }`}
            >
              Teams
              {activeTab === "teams" && (
                <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-neutral-900" />
              )}
            </button>
            <button
              onClick={() => setActiveTab("general")}
              className={`relative pb-3 text-[14px] font-medium transition-colors whitespace-nowrap ${
                activeTab === "general"
                  ? "text-neutral-900"
                  : "text-neutral-500 hover:text-neutral-700"
              }`}
            >
              General
              {activeTab === "general" && (
                <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-neutral-900" />
              )}
            </button>
          </div>
        </div>
      </header>

      <div className="px-10 py-6">
        {activeTab === "general" && (
          <div className="max-w-2xl">
            <form onSubmit={handleUpdatePractice} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label
                    htmlFor="practice_name"
                    className="text-[13px] font-medium text-neutral-700"
                  >
                    Practice Name
                  </Label>
                  <Input
                    id="practice_name"
                    type="text"
                    value={practiceName}
                    onChange={(e) => setPracticeName(e.target.value)}
                    disabled={isUpdating}
                    className="h-9 border-neutral-200 bg-white text-[14px] text-neutral-900 placeholder:text-neutral-400"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label
                    htmlFor="practice_region"
                    className="text-[13px] font-medium text-neutral-700"
                  >
                    Practice Region / Timezone
                  </Label>
                  <Select
                    value={practiceRegion}
                    onValueChange={setPracticeRegion}
                    disabled={isUpdating}
                  >
                    <SelectTrigger className="h-9 border-neutral-200 bg-white text-[14px] text-neutral-900">
                      <SelectValue placeholder="Select a region" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="America/New_York">
                        Eastern Time (America/New_York)
                      </SelectItem>
                      <SelectItem value="America/Chicago">
                        Central Time (America/Chicago)
                      </SelectItem>
                      <SelectItem value="America/Denver">
                        Mountain Time (America/Denver)
                      </SelectItem>
                      <SelectItem value="America/Los_Angeles">
                        Pacific Time (America/Los_Angeles)
                      </SelectItem>
                      <SelectItem value="America/Anchorage">
                        Alaska Time (America/Anchorage)
                      </SelectItem>
                      <SelectItem value="Pacific/Honolulu">
                        Hawaii Time (Pacific/Honolulu)
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button
                type="submit"
                disabled={isUpdating}
                className="h-9 rounded-none bg-black px-5 text-[14px] font-medium text-white hover:bg-neutral-800"
              >
                {isUpdating ? <Spinner /> : "Save Changes"}
              </Button>
            </form>
          </div>
        )}

        {activeTab === "teams" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <p className="text-[14px] text-neutral-500">
                Create teams to organize and filter calls on the dashboard.
              </p>
              <Button
                onClick={() => setAddTeamDialogOpen(true)}
                className="h-9 rounded-none bg-black px-5 text-[14px] hover:bg-neutral-800"
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Team
              </Button>
            </div>

            <div className="grid grid-cols-2 gap-4 xl:grid-cols-3 2xl:grid-cols-4">
              {teams.map((team) => (
                <TeamCard
                  key={team.id}
                  team={team}
                  users={users}
                  onEdit={() => openEditDialog(team)}
                  onDelete={() => openDeleteDialog(team)}
                  onAddMember={(userId) => handleAddMember(team.id, userId)}
                  onRemoveMember={(userId) => handleRemoveMember(team.id, userId)}
                />
              ))}
              {teams.length === 0 && (
                <div
                  className="col-span-full flex h-48 items-center justify-center rounded-lg border border-neutral-100"
                  style={{ backgroundColor: "#FDFDFD" }}
                >
                  <div className="text-center">
                    <p className="text-[14px] text-neutral-500">No teams configured</p>
                    <Button
                      variant="link"
                      onClick={() => setAddTeamDialogOpen(true)}
                      className="mt-2 text-[14px]"
                    >
                      Add your first team
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <Dialog open={addTeamDialogOpen} onOpenChange={setAddTeamDialogOpen}>
        <DialogContent className="max-w-md border-neutral-200 bg-white">
          <DialogHeader>
            <DialogTitle className="text-2xl font-semibold text-neutral-900">Add Team</DialogTitle>
            <DialogDescription className="text-[14px] text-neutral-500">
              Create a new team to categorize calls.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="team_title" className="text-[13px] font-medium text-neutral-700">
                Title
              </Label>
              <Input
                id="team_title"
                type="text"
                value={newTeamTitle}
                onChange={(e) => setNewTeamTitle(e.target.value)}
                placeholder="Retina"
                className="h-9 border-neutral-200 bg-white text-[14px] text-neutral-900 placeholder:text-neutral-400"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="team_description" className="text-[13px] font-medium text-neutral-700">
                Description
              </Label>
              <Textarea
                id="team_description"
                value={newTeamDescription}
                onChange={(e) => setNewTeamDescription(e.target.value)}
                placeholder="Retina department — Dr. Bertolucci, Dr. Prescott, Dr. Thinda, Dr. Teasley, Dr. Mehta"
                className="min-h-[80px] border-neutral-200 bg-white text-[14px] text-neutral-900 placeholder:text-neutral-400"
              />
            </div>
          </div>
          <DialogFooter className="gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setAddTeamDialogOpen(false)}
              disabled={loadingAction}
              className="h-9 rounded-none border-neutral-200 text-[14px] font-medium text-neutral-900 hover:bg-neutral-50"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddTeam}
              disabled={!newTeamTitle.trim() || loadingAction}
              className="h-9 rounded-none bg-black px-5 text-[14px] font-medium text-white hover:bg-neutral-800"
            >
              {loadingAction ? <Spinner /> : "Add Team"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={editTeamDialogOpen} onOpenChange={setEditTeamDialogOpen}>
        <DialogContent className="max-w-md border-neutral-200 bg-white">
          <DialogHeader>
            <DialogTitle className="text-2xl font-semibold text-neutral-900">Edit Team</DialogTitle>
            <DialogDescription className="text-[14px] text-neutral-500">
              Update the team details.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit_team_title" className="text-[13px] font-medium text-neutral-700">
                Title
              </Label>
              <Input
                id="edit_team_title"
                type="text"
                value={editTeamTitle}
                onChange={(e) => setEditTeamTitle(e.target.value)}
                className="h-9 border-neutral-200 bg-white text-[14px] text-neutral-900 placeholder:text-neutral-400"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit_team_description" className="text-[13px] font-medium text-neutral-700">
                Description
              </Label>
              <Textarea
                id="edit_team_description"
                value={editTeamDescription}
                onChange={(e) => setEditTeamDescription(e.target.value)}
                className="min-h-[80px] border-neutral-200 bg-white text-[14px] text-neutral-900 placeholder:text-neutral-400"
              />
            </div>
          </div>
          <DialogFooter className="gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setEditTeamDialogOpen(false)}
              disabled={loadingAction}
              className="h-9 rounded-none border-neutral-200 text-[14px] font-medium text-neutral-900 hover:bg-neutral-50"
            >
              Cancel
            </Button>
            <Button
              onClick={handleEditTeam}
              disabled={!editTeamTitle.trim() || loadingAction}
              className="h-9 rounded-none bg-black px-5 text-[14px] font-medium text-white hover:bg-neutral-800"
            >
              {loadingAction ? <Spinner /> : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={deleteTeamDialogOpen}
        onOpenChange={(open) => {
          if (!open && loadingAction) return;
          setDeleteTeamDialogOpen(open);
        }}
      >
        <AlertDialogContent className="max-w-sm border-neutral-200 bg-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-2xl font-semibold text-neutral-900">
              Delete Team
            </AlertDialogTitle>
            <AlertDialogDescription className="text-[14px] text-neutral-500">
              Are you sure you want to delete {selectedTeam?.title}? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              disabled={loadingAction}
              className="h-9 rounded-none border-neutral-200 text-[14px] font-medium text-neutral-900 hover:bg-neutral-50"
            >
              Cancel
            </AlertDialogCancel>
            <Button
              onClick={handleDeleteTeam}
              disabled={loadingAction}
              className="h-9 rounded-none bg-red-600 px-5 text-[14px] font-medium text-white hover:bg-red-700"
            >
              {loadingAction ? <Spinner /> : "Delete"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
