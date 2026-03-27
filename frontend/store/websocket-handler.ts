import { AppDispatch } from "./index";
import { addCall, updateCall, callDeleted } from "./slices/calls-slice";
import { practiceUpdated } from "./slices/practice-slice";
import { userCreated, userUpdated, userDeleted } from "./slices/users-slice";
import {
  invitationCreated,
  invitationAccepted,
  invitationCanceled,
} from "./slices/invitations-slice";
import { CallDetail } from "@/types/call";
import { Practice } from "@/types/practice";
import { User } from "@/types/user";
import { Invitation } from "@/types/invitation";

interface WebSocketEvent {
  type: string;
  data: unknown;
}

export function handleWebSocketEvent(
  event: WebSocketEvent,
  dispatch: AppDispatch
): void {
  switch (event.type) {
    case "call_created":
      dispatch(addCall(event.data as CallDetail));
      break;

    case "call_updated":
      dispatch(updateCall(event.data as Partial<CallDetail> & { id: string }));
      break;

    case "call_deleted":
      dispatch(callDeleted((event.data as { id: string }).id));
      break;

    case "practice_updated":
      dispatch(practiceUpdated(event.data as Practice));
      break;

    case "user_created":
      dispatch(userCreated(event.data as User));
      break;

    case "user_updated":
      dispatch(userUpdated(event.data as User));
      break;

    case "user_deleted":
      dispatch(userDeleted((event.data as { id: string }).id));
      break;

    case "invitation_created":
      dispatch(invitationCreated(event.data as Invitation));
      break;

    case "invitation_accepted":
      dispatch(invitationAccepted(event.data as Invitation));
      break;

    case "invitation_canceled":
      dispatch(invitationCanceled(event.data as Invitation));
      break;

    default:
      break;
  }
}
