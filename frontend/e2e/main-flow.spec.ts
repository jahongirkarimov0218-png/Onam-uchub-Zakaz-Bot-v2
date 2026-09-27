// Main E2E flow (spec.md stories 58/59, ticket 07):
// /app catalog -> add product -> cart -> checkout (manual phone, pickup) ->
// success number -> mock records the admin sendMessage naming the order ->
// /admin as admin -> open the order -> "Qabul qilindi" -> mock records the
// customer sendMessage with the new status and the admin editMessageText.
// No real Telegram network call anywhere: TELEGRAM_API_BASE (set by
// global-setup) points both bots at ./mock-telegram.ts for the whole run.
import { test, expect } from "@playwright/test";
import { openMiniApp, waitForMockCall } from "./helpers";
import { ADMIN_BOT_TOKEN, ADMIN_TG_ID, CUSTOMER_BOT_TOKEN, CUSTOMER_TG_ID } from "./constants";

test("catalog -> cart -> checkout -> admin accepts -> customer notified", async ({ browser }) => {
  const customerContext = await browser.newContext();
  const customerPage = await openMiniApp(
    customerContext,
    "/app/",
    { id: CUSTOMER_TG_ID, first_name: "Mijoz", last_name: "Testov" },
    CUSTOMER_BOT_TOKEN
  );

  // Catalog: seeded products load, add the first available one to the cart.
  const addToCartButton = customerPage.getByRole("button", { name: "Savatga qo'shish" }).first();
  await expect(addToCartButton).toBeVisible();
  await addToCartButton.click();

  // Cart
  await customerPage.getByRole("button", { name: "Savat", exact: true }).click();
  await expect(customerPage.getByText("Jami")).toBeVisible();
  await customerPage.getByRole("button", { name: "Buyurtma berish" }).click();

  // Checkout: manual phone entry (no requestContact), pickup delivery
  await customerPage.getByLabel("Ismingiz").fill("Mijoz Testov");
  await customerPage.getByLabel("Telefon").fill("+998901234567");
  await customerPage.getByLabel("Olib ketish").check();
  await customerPage.getByRole("button", { name: "Buyurtma berish" }).click();

  // Success screen shows the order number
  await expect(customerPage.getByText("Buyurtma qabul qilindi")).toBeVisible();
  const orderNumberText = await customerPage.getByText(/Buyurtma raqami #\d+/).textContent();
  const orderId = Number(orderNumberText?.match(/#(\d+)/)?.[1]);
  expect(Number.isInteger(orderId) && orderId > 0).toBe(true);

  // The admin bot received a sendMessage naming this order
  const adminNotice = await waitForMockCall(
    (call) =>
      call.method === "sendMessage" &&
      call.token === ADMIN_BOT_TOKEN &&
      Number(call.fields.chat_id) === ADMIN_TG_ID &&
      (call.fields.text ?? "").includes(`Zakaz #${orderId}`)
  );
  expect(adminNotice.fields.text).toContain(`Zakaz #${orderId}`);

  await customerContext.close();

  // Admin Mini App: open the order, accept it ("Qabul qilindi")
  const adminContext = await browser.newContext();
  const adminPage = await openMiniApp(adminContext, "/admin/", { id: ADMIN_TG_ID, first_name: "Admin" }, ADMIN_BOT_TOKEN);

  await adminPage.getByRole("button", { name: `#${orderId}`, exact: true }).click();
  await expect(adminPage.getByRole("heading", { name: `#${orderId}`, exact: true })).toBeVisible();
  await adminPage.getByRole("button", { name: "Qabul qilindi", exact: true }).click();
  await expect(adminPage.getByText("Qabul qilindi").first()).toBeVisible();

  // The customer bot was notified of the new status
  const customerNotice = await waitForMockCall(
    (call) =>
      call.method === "sendMessage" &&
      call.token === CUSTOMER_BOT_TOKEN &&
      Number(call.fields.chat_id) === CUSTOMER_TG_ID &&
      (call.fields.text ?? "").includes("Qabul qilindi")
  );
  expect(customerNotice.fields.text).toContain(`#${orderId}`);

  // ...and the admin's order card message was edited in place
  const adminEdit = await waitForMockCall(
    (call) =>
      call.method === "editMessageText" &&
      call.token === ADMIN_BOT_TOKEN &&
      (call.fields.text ?? "").includes("Qabul qilindi")
  );
  expect(adminEdit.fields.text).toContain(`Zakaz #${orderId}`);

  await adminContext.close();
});
