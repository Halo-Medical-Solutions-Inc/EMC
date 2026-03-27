"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Edit, MoreVertical, Plus, RotateCcw, Trash2, X } from "lucide-react";
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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { useAppDispatch, useAppSelector } from "@/store";
import {
  createInvitation,
  cancelInvitation,
  resendInvitation,
} from "@/store/slices/invitations-slice";
import { updateUser, deleteUser } from "@/store/slices/users-slice";
import { UserRole } from "@/types/user";
import { Invitation } from "@/types/invitation";
import { User } from "@/types/user";

const REGION_TO_TIMEZONE: Record<string, string> = {
  PST: "America/Los_Angeles",
  MST: "America/Denver",
  CST: "America/Chicago",
  EST: "America/New_York",
  Pacific: "America/Los_Angeles",
  Mountain: "America/Denver",
  Central: "America/Chicago",
  Eastern: "America/New_York",
  "America/Los_Angeles": "America/Los_Angeles",
  "America/Denver": "America/Denver",
  "America/Chicago": "America/Chicago",
  "America/New_York": "America/New_York",
};

function formatName(name: string): string {
  if (!name?.trim()) return name || "";
  return name
    .trim()
    .split(/\s+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

export default function TeamSettingsPage() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const { users } = useAppSelector((state) => state.users);
  const { invitations } = useAppSelector((state) => state.invitations);
  const { practice } = useAppSelector((state) => state.practice);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedInvitationId, setSelectedInvitationId] = useState<
    string | null
  >(null);
  const [copiedLink, setCopiedLink] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [cancelInviteDialogOpen, setCancelInviteDialogOpen] = useState(false);
  const [resendInviteDialogOpen, setResendInviteDialogOpen] = useState(false);
  const [inviteFormData, setInviteFormData] = useState<{
    email: string;
    role: UserRole;
  }>({ email: "", role: UserRole.STAFF });
  const [editFormData, setEditFormData] = useState<{
    full_name: string;
    role: UserRole;
    region: string | null;
  }>({ full_name: "", role: UserRole.STAFF, region: "" });
  const [loadingInvite, setLoadingInvite] = useState(false);
  const [loadingUpdate, setLoadingUpdate] = useState(false);
  const [loadingDelete, setLoadingDelete] = useState(false);
  const [cancelingInvite, setCancelingInvite] = useState(false);
  const [resendingInvite, setResendingInvite] = useState(false);

  useEffect(() => {
    if (!user) {
      router.push("/login");
    }
  }, [user, router]);

  async function handleInviteUser(): Promise<void> {
    setLoadingInvite(true);
    try {
      const result = await dispatch(createInvitation(inviteFormData)).unwrap();
      if (result.devLink) {
        toast.success("Invitation sent successfully", {
          description: "Development mode: copy the invitation link below",
          action: {
            label: copiedLink === result.devLink ? "Copied!" : "Copy Link",
            onClick: async () => {
              try {
                await navigator.clipboard.writeText(result.devLink!);
                setCopiedLink(result.devLink!);
                setTimeout(() => setCopiedLink(null), 2000);
              } catch {
                toast.error("Failed to copy link");
              }
            },
          },
        });
        toast.info(result.devLink, { duration: 10000 });
      } else {
        toast.success("Invitation sent successfully");
      }
    } catch (error: unknown) {
      const errorMessage = error as string;
      toast.error(errorMessage || "Failed to send invitation");
    } finally {
      setLoadingInvite(false);
      setInviteDialogOpen(false);
      setInviteFormData({ email: "", role: UserRole.STAFF });
    }
  }

  async function handleUpdateUser(): Promise<void> {
    if (!editingUser) return;
    setLoadingUpdate(true);
    try {
      const updateData: { full_name: string; role: UserRole; region?: string } =
        {
          full_name: editFormData.full_name,
          role: editFormData.role,
          ...(editFormData.region ? { region: editFormData.region } : {}),
        };
      await dispatch(
        updateUser({ userId: editingUser.id, data: updateData })
      ).unwrap();
      toast.success("User updated successfully");
    } catch (error: unknown) {
      const errorMessage = error as string;
      toast.error(errorMessage || "Failed to update user");
    } finally {
      setLoadingUpdate(false);
      setEditingUser(null);
    }
  }

  async function handleDeleteUser(): Promise<void> {
    if (!selectedUserId) return;
    setLoadingDelete(true);
    try {
      await dispatch(deleteUser(selectedUserId)).unwrap();
      toast.success("User deleted successfully");
    } catch (error: unknown) {
      const errorMessage = error as string;
      toast.error(errorMessage || "Failed to delete user");
    } finally {
      setLoadingDelete(false);
      setDeleteDialogOpen(false);
      setSelectedUserId(null);
    }
  }

  async function handleCancelInvitation(): Promise<void> {
    if (!selectedInvitationId) return;
    setCancelingInvite(true);
    try {
      await dispatch(cancelInvitation(selectedInvitationId)).unwrap();
      toast.success("Invitation cancelled successfully");
    } catch (error: unknown) {
      const errorMessage = error as string;
      toast.error(errorMessage || "Failed to cancel invitation");
    } finally {
      setCancelingInvite(false);
      setCancelInviteDialogOpen(false);
      setSelectedInvitationId(null);
    }
  }

  async function handleResendInvitation(): Promise<void> {
    if (!selectedInvitationId) return;
    setResendingInvite(true);
    try {
      const result = await dispatch(
        resendInvitation(selectedInvitationId)
      ).unwrap();
      if (result.devLink) {
        toast.success("Invitation resent successfully", {
          description: "Development mode: copy the invitation link below",
          action: {
            label: copiedLink === result.devLink ? "Copied!" : "Copy Link",
            onClick: async () => {
              try {
                await navigator.clipboard.writeText(result.devLink!);
                setCopiedLink(result.devLink!);
                setTimeout(() => setCopiedLink(null), 2000);
              } catch {
                toast.error("Failed to copy link");
              }
            },
          },
        });
        toast.info(result.devLink, { duration: 10000 });
      } else {
        toast.success("Invitation resent successfully");
      }
    } catch (error: unknown) {
      const errorMessage = error as string;
      toast.error(errorMessage || "Failed to resend invitation");
    } finally {
      setResendingInvite(false);
      setResendInviteDialogOpen(false);
      setSelectedInvitationId(null);
    }
  }

  function formatDateTime(
    utcDateString: string,
    userRegion?: string | null
  ): string {
    try {
      const utcDate = new Date(utcDateString);
      const region = userRegion || user?.region || null;
      const timezone = region
        ? REGION_TO_TIMEZONE[region] || region
        : "America/Los_Angeles";
      const dateFormatter = new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        timeZone: timezone,
      });
      const timeFormatter = new Intl.DateTimeFormat("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
        timeZone: timezone,
      });
      const datePart = dateFormatter.format(utcDate);
      const timePart = timeFormatter.format(utcDate);
      return `${datePart} at ${timePart}`;
    } catch {
      return utcDateString;
    }
  }

  function formatLastActive(dateStr: string | null): string {
    if (!dateStr) return "Not recorded";
    return formatDateTime(dateStr, user?.region);
  }

  function getRoleBadge(role: UserRole) {
    if (role === UserRole.ADMIN || role === UserRole.SUPER_ADMIN) {
      return (
        <Badge className="border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-50">
          Admin
        </Badge>
      );
    }
    return (
      <Badge className="border-purple-200 bg-purple-50 text-purple-700 hover:bg-purple-50">
        Staff
      </Badge>
    );
  }

  function getStatusBadge(invitation: Invitation) {
    if (invitation.accepted_at) {
      return (
        <Badge className="border-green-200 bg-green-50 text-green-700 hover:bg-green-50">
          Accepted
        </Badge>
      );
    }
    if (invitation.canceled_at) {
      return (
        <Badge className="border-gray-200 bg-gray-50 text-gray-700 hover:bg-gray-50">
          Canceled
        </Badge>
      );
    }
    return (
      <Badge className="border-yellow-200 bg-yellow-50 text-yellow-700 hover:bg-yellow-50">
        Pending
      </Badge>
    );
  }

  const pendingInvitations = invitations.filter(
    (inv) => !inv.accepted_at && !inv.canceled_at
  );
  const isAdmin =
    user?.role === UserRole.ADMIN || user?.role === UserRole.SUPER_ADMIN;

  if (!user) return null;

  return (
    <>
      <header className="border-b border-neutral-100 bg-white">
        <div className="px-10 py-8">
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="text-[24px] font-semibold tracking-tight text-neutral-900">
                My Team
              </h1>
              <p className="mt-1 text-[15px] text-neutral-500">
                {isAdmin
                  ? "Manage your team members and send invitations."
                  : "View your team members."}
              </p>
            </div>
            {isAdmin && (
              <Button
                onClick={() => setInviteDialogOpen(true)}
                className="h-9 rounded-none bg-black px-5 text-[14px] hover:bg-neutral-800"
              >
                <Plus className="mr-2 h-4 w-4" />
                Invite User
              </Button>
            )}
          </div>
        </div>
      </header>

      <div className="px-10 py-6">
        {users.length > 0 && (
          <div className="mb-8">
            <h3 className="mb-3 text-sm font-medium text-neutral-700">
              Active Members
            </h3>
            <div
              className="rounded-lg border border-neutral-100"
              style={{ backgroundColor: "#FDFDFD" }}
            >
              <div
                className={`grid ${isAdmin ? "grid-cols-[1fr_1fr_1fr_40px]" : "grid-cols-[1fr_1fr_1fr]"} gap-4 border-b border-neutral-100 px-4 py-3 text-[13px] font-medium text-neutral-500`}
              >
                <div>Name</div>
                <div>Role</div>
                <div>Last Active</div>
                {isAdmin && <div></div>}
              </div>

              {[...users].sort((a, b) => {
                const aIsAdmin = a.role === UserRole.ADMIN || a.role === UserRole.SUPER_ADMIN;
                const bIsAdmin = b.role === UserRole.ADMIN || b.role === UserRole.SUPER_ADMIN;
                if (aIsAdmin && !bIsAdmin) return 1;
                if (!aIsAdmin && bIsAdmin) return -1;
                return a.full_name.localeCompare(b.full_name);
              }).map((usr) => (
                <div
                  key={usr.id}
                  className={`group grid ${isAdmin ? "grid-cols-[1fr_1fr_1fr_40px]" : "grid-cols-[1fr_1fr_1fr]"} gap-4 border-b border-neutral-50 px-4 py-4 transition-colors hover:bg-neutral-50 last:border-b-0`}
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="text-[14px] font-medium text-neutral-900">
                      {formatName(usr.full_name)}
                    </div>
                    <div className="text-[12px] text-neutral-500">
                      {usr.email}
                    </div>
                  </div>
                  <div className="flex items-center text-[13px]">
                    {getRoleBadge(usr.role)}
                  </div>
                  <div className="flex items-center text-[13px] text-neutral-600">
                    {formatLastActive(usr.last_active_at)}
                  </div>
                  {isAdmin && (
                    <div className="flex items-center justify-end">
                      {usr.role !== UserRole.SUPER_ADMIN && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                            >
                              <MoreVertical className="h-4 w-4 text-neutral-500" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-40">
                            <DropdownMenuItem
                              onClick={() => {
                                setEditingUser(usr);
                                setEditFormData({
                                  full_name: usr.full_name,
                                  role: usr.role,
                                  region: usr.region,
                                });
                              }}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              <span>Edit</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              variant="destructive"
                              onClick={() => {
                                setSelectedUserId(usr.id);
                                setDeleteDialogOpen(true);
                              }}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              <span>Delete</span>
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {pendingInvitations.length > 0 && (
          <div>
            <h3 className="mb-3 text-sm font-medium text-neutral-700">
              Pending Invitations
            </h3>
            <div
              className="rounded-lg border border-neutral-100"
              style={{ backgroundColor: "#FDFDFD" }}
            >
              <div
                className={`grid ${isAdmin ? "grid-cols-[1fr_1fr_1fr_1fr_40px]" : "grid-cols-[1fr_1fr_1fr_1fr]"} gap-4 border-b border-neutral-100 px-4 py-3 text-[13px] font-medium text-neutral-500`}
              >
                <div>Email</div>
                <div>Role</div>
                <div>Expires At</div>
                <div>Status</div>
                {isAdmin && <div></div>}
              </div>

              {pendingInvitations.map((invitation) => (
                <div
                  key={invitation.id}
                  className={`group grid ${isAdmin ? "grid-cols-[1fr_1fr_1fr_1fr_40px]" : "grid-cols-[1fr_1fr_1fr_1fr]"} gap-4 border-b border-neutral-50 px-4 py-4 transition-colors hover:bg-neutral-50 last:border-b-0`}
                >
                  <div className="flex items-center text-[14px] font-medium text-neutral-900">
                    {invitation.email}
                  </div>
                  <div className="flex items-center text-[13px]">
                    {getRoleBadge(invitation.role)}
                  </div>
                  <div className="flex items-center text-[13px] text-neutral-500">
                    {formatDateTime(invitation.expires_at, user?.region)}
                  </div>
                  <div className="flex items-center text-[13px]">
                    {getStatusBadge(invitation)}
                  </div>
                  {isAdmin && (
                    <div className="flex items-center justify-end">
                      <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                        >
                          <MoreVertical className="h-4 w-4 text-neutral-500" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-40">
                        <DropdownMenuItem
                          onClick={() => {
                            setSelectedInvitationId(invitation.id);
                            setResendInviteDialogOpen(true);
                          }}
                        >
                          <RotateCcw className="mr-2 h-4 w-4" />
                          <span>Resend</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() => {
                            setSelectedInvitationId(invitation.id);
                            setCancelInviteDialogOpen(true);
                          }}
                        >
                          <X className="mr-2 h-4 w-4" />
                          <span>Cancel</span>
                        </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {users.length === 0 && pendingInvitations.length === 0 && (
            <div
              className="rounded-lg border border-neutral-100 p-12 text-center"
              style={{ backgroundColor: "#FDFDFD" }}
            >
              <p className="text-[14px] text-neutral-500">
                No team members found
              </p>
            </div>
          )}
      </div>

      <Dialog
        open={editingUser !== null}
        onOpenChange={() => setEditingUser(null)}
      >
        <DialogContent className="max-w-md border-neutral-200 bg-white">
          <DialogHeader>
            <DialogTitle className="text-2xl font-semibold text-neutral-900">
              Edit User
            </DialogTitle>
            <DialogDescription className="text-[14px] text-neutral-500">
              Update team member details.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label
                htmlFor="edit_role"
                className="text-[13px] font-medium text-neutral-700"
              >
                Role
              </Label>
              <Select
                value={editFormData.role}
                onValueChange={(value) =>
                  setEditFormData({ ...editFormData, role: value as UserRole })
                }
              >
                <SelectTrigger className="h-9 border-neutral-200 bg-white text-[14px] text-neutral-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={UserRole.STAFF}>Staff</SelectItem>
                  <SelectItem value={UserRole.ADMIN}>Admin</SelectItem>
                  <SelectItem value={UserRole.SUPER_ADMIN}>
                    Super Admin
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter className="gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setEditingUser(null)}
              disabled={loadingUpdate}
              className="h-9 rounded-none border-neutral-200 text-[14px] font-medium text-neutral-900 hover:bg-neutral-50"
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdateUser}
              disabled={loadingUpdate}
              className="h-9 rounded-none bg-black px-5 text-[14px] font-medium text-white hover:bg-neutral-800"
            >
              {loadingUpdate ? <Spinner /> : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={deleteDialogOpen}
        onOpenChange={(open) => {
          if (!open && loadingDelete) return;
          setDeleteDialogOpen(open);
        }}
      >
        <AlertDialogContent className="max-w-sm border-neutral-200 bg-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-2xl font-semibold text-neutral-900">
              Delete User
            </AlertDialogTitle>
            <AlertDialogDescription className="text-[14px] text-neutral-500">
              Are you sure you want to delete this user? This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              disabled={loadingDelete}
              className="h-9 rounded-none border-neutral-200 text-[14px] font-medium text-neutral-900 hover:bg-neutral-50"
            >
              Cancel
            </AlertDialogCancel>
            <Button
              onClick={handleDeleteUser}
              disabled={loadingDelete}
              className="h-9 rounded-none bg-red-600 px-5 text-[14px] font-medium text-white hover:bg-red-700"
            >
              {loadingDelete ? <Spinner /> : "Delete"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={cancelInviteDialogOpen}
        onOpenChange={(open) => {
          if (!open && cancelingInvite) return;
          setCancelInviteDialogOpen(open);
        }}
      >
        <AlertDialogContent className="max-w-sm border-neutral-200 bg-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-2xl font-semibold text-neutral-900">
              Cancel Invitation
            </AlertDialogTitle>
            <AlertDialogDescription className="text-[14px] text-neutral-500">
              Are you sure you want to cancel this invitation? This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              disabled={cancelingInvite}
              className="h-9 rounded-none border-neutral-200 text-[14px] font-medium text-neutral-900 hover:bg-neutral-50"
            >
              Cancel
            </AlertDialogCancel>
            <Button
              onClick={handleCancelInvitation}
              disabled={cancelingInvite}
              className="h-9 rounded-none bg-red-600 px-5 text-[14px] font-medium text-white hover:bg-red-700"
            >
              {cancelingInvite ? <Spinner /> : "Cancel Invitation"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={resendInviteDialogOpen}
        onOpenChange={(open) => {
          if (!open && resendingInvite) return;
          setResendInviteDialogOpen(open);
        }}
      >
        <AlertDialogContent className="max-w-sm border-neutral-200 bg-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-2xl font-semibold text-neutral-900">
              Resend Invitation
            </AlertDialogTitle>
            <AlertDialogDescription className="text-[14px] text-neutral-500">
              This will send a new invitation email. The old invitation link
              will no longer work.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              disabled={resendingInvite}
              className="h-9 rounded-none border-neutral-200 text-[14px] font-medium text-neutral-900 hover:bg-neutral-50"
            >
              Cancel
            </AlertDialogCancel>
            <Button
              onClick={handleResendInvitation}
              disabled={resendingInvite}
              className="h-9 rounded-none bg-black px-5 text-[14px] font-medium text-white hover:bg-neutral-800"
            >
              {resendingInvite ? <Spinner /> : "Resend"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
        <DialogContent className="max-w-md border-neutral-200 bg-white">
          <DialogHeader>
            <DialogTitle className="text-2xl font-semibold text-neutral-900">
              Invite User
            </DialogTitle>
            <DialogDescription className="text-[14px] text-neutral-500">
              Send an invitation to join your practice.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label
                htmlFor="invite_email"
                className="text-[13px] font-medium text-neutral-700"
              >
                Email
              </Label>
              <Input
                id="invite_email"
                type="email"
                value={inviteFormData.email}
                onChange={(e) =>
                  setInviteFormData({
                    ...inviteFormData,
                    email: e.target.value,
                  })
                }
                placeholder="email@example.com"
                className="h-9 border-neutral-200 bg-white text-[14px] text-neutral-900 placeholder:text-neutral-400"
              />
            </div>
            <div className="space-y-2">
              <Label
                htmlFor="invite_role"
                className="text-[13px] font-medium text-neutral-700"
              >
                Role
              </Label>
              <Select
                value={inviteFormData.role}
                onValueChange={(value) =>
                  setInviteFormData({
                    ...inviteFormData,
                    role: value as UserRole,
                  })
                }
              >
                <SelectTrigger className="h-9 border-neutral-200 bg-white text-[14px] text-neutral-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={UserRole.STAFF}>Staff</SelectItem>
                  <SelectItem value={UserRole.ADMIN}>Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter className="gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setInviteDialogOpen(false)}
              disabled={loadingInvite}
              className="h-9 rounded-none border-neutral-200 text-[14px] font-medium text-neutral-900 hover:bg-neutral-50"
            >
              Cancel
            </Button>
            <Button
              onClick={handleInviteUser}
              disabled={!inviteFormData.email || loadingInvite}
              className="h-9 rounded-none bg-black px-5 text-[14px] font-medium text-white hover:bg-neutral-800"
            >
              {loadingInvite ? <Spinner /> : "Send Invitation"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
