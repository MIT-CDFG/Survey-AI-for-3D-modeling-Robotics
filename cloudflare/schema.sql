-- One row per counted page. Seeded with 1800, the last Busuanzi total the owner recalls.
CREATE TABLE IF NOT EXISTS page_views (
  page  TEXT PRIMARY KEY,
  views INTEGER NOT NULL CHECK (views >= 0)
);
INSERT OR IGNORE INTO page_views (page, views)
VALUES ('https://mit-cdfg.github.io/Survey-AI-for-3D-modeling-Robotics/', 1800);
