BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS `wallets` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	`wallet_uuid`	TEXT NOT NULL,
	`wallet_name`	TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS `tasks` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	`task_id`	TEXT NOT NULL,
	`content`	TEXT NOT NULL,
	`description`	TEXT,
	`date_added`	INTEGER NOT NULL,
	`date_due`	INTEGER NOT NULL,
	`date_completed`	INTEGER NOT NULL,
	`reminder`	INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS `expenses` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	`expense_id`	TEXT NOT NULL,
	`wallet_id`	TEXT NOT NULL,
	`category_id`	TEXT NOT NULL,
	`content`	TEXT NOT NULL,
	`description`	TEXT,
	`date_added`	INTEGER NOT NULL,
	`date_spent`	INTEGER NOT NULL,
	`amount`	REAL NOT NULL,
	`is_income`	INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS `categories` (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	`category_uuid`	TEXT NOT NULL,
	`category_name`	TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS `index_wallets_wallet_uuid` ON `wallets` (
	`wallet_uuid`
);
CREATE UNIQUE INDEX IF NOT EXISTS `index_tasks_task_id` ON `tasks` (
	`task_id`
);
CREATE UNIQUE INDEX IF NOT EXISTS `index_expenses_expense_id` ON `expenses` (
	`expense_id`
);
CREATE UNIQUE INDEX IF NOT EXISTS `index_categories_category_uuid` ON `categories` (
	`category_uuid`
);
COMMIT;
