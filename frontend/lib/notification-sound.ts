import { playSound } from "@/lib/sound-engine";
import { notificationPopSound } from "@/lib/sounds/notification-pop";

export async function playNotificationSound(): Promise<void> {
  try {
    await playSound(notificationPopSound.dataUri, { volume: 0.7 });
  } catch {
    // Browser may block autoplay before user interaction
  }
}
