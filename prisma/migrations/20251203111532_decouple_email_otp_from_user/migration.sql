/*
  Warnings:

  - You are about to drop the column `userId` on the `EmailOtp` table. All the data in the column will be lost.
  - Added the required column `email` to the `EmailOtp` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "EmailOtp" DROP CONSTRAINT "EmailOtp_userId_fkey";

-- DropIndex
DROP INDEX "EmailOtp_userId_purpose_used_idx";

-- AlterTable
ALTER TABLE "EmailOtp" DROP COLUMN "userId",
ADD COLUMN     "email" TEXT NOT NULL,
ADD COLUMN     "payload" JSONB;

-- CreateIndex
CREATE INDEX "EmailOtp_email_purpose_used_idx" ON "EmailOtp"("email", "purpose", "used");
