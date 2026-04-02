import { AppDispatch } from "./index";
import { addCall, updateCall, callDeleted } from "./slices/calls-slice";
import { incrementUnreadCount } from "./slices/mentions-slice";
import {
  invitationCreated,
  invitationAccepted,
  invitationCanceled,
} from "./slices/invitations-slice";
import {
  conversationCreated,
  conversationDeleted,
  conversationMemberRemoved,
  messageDeleted,
  messageReactionsUpdated,
  messageReceived,
  messageUpdated,
} from "./slices/messages-slice";
import { practiceUpdated } from "./slices/practice-slice";
import { userCreated, userUpdated, userDeleted } from "./slices/users-slice";
import { CallDetail } from "@/types/call";
import { Invitation } from "@/types/invitation";
import { ChatMessage, Conversation } from "@/types/message";
import { Practice } from "@/types/practice";
import { User } from "@/types/user";

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

    case "message_created":
      dispatch(messageReceived(event.data as ChatMessage));
      break;

    case "message_updated":
      dispatch(messageUpdated(event.data as ChatMessage));
      break;

    case "message_deleted":
      dispatch(messageDeleted(event.data as { id: string; conversation_id: string }));
      break;

    case "message_reactions_updated":
      dispatch(messageReactionsUpdated(event.data as ChatMessage));
      break;

    case "conversation_created":
      dispatch(conversationCreated(event.data as Conversation));
      break;

    case "conversation_deleted":
      dispatch(conversationDeleted((event.data as { id: string }).id));
      break;

    case "mention_created":
      dispatch(incrementUnreadCount());
      break;

    case "conversation_member_removed":
      dispatch(
        conversationMemberRemoved(
          event.data as { conversation_id: string; user_id: string },
        ),
      );
      break;

    default:
      break;
  }
}
