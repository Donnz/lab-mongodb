CREATE KEYSPACE disputes
  WITH REPLICATION = { 
   'class' : 'SimpleStrategy', 
   'replication_factor' : 1 
  };

CREATE TYPE disputes.attachment (
  artifactId text,
  mimeType text,
  extFileName text,
  description text
);

CREATE TYPE disputes.proposal (
  gmtSubmitted timestamp,
  richTextReport text,
  proposedSolution text,
  status text,
  attachments list<frozen<attachment>>
);

CREATE TYPE disputes.negotiationRound (
  initialProposal frozen<proposal>,
  counterProposal frozen<proposal>
);

CREATE TYPE disputes.resolution (
  status text,
  arbitratorId text,
  decision text,
  firstRound frozen<negotiationRound>,
  lastRound frozen<negotiationRound>,
  gmtArbitrated timestamp,
  gmtArbitratorAssigned timestamp
);

CREATE TYPE disputes.itemPrice (
  cent int,
  currency text
);

CREATE TYPE disputes.item (
  itemPrice frozen<itemPrice>,
  supportFreeReturn boolean,
  itemCount int,
  itemId text,
  skuId text,
  skuValue text,
  tradeSnapshotUrl text,
  ParentOrderId text
);

USE disputes;

CREATE TABLE disputes (
  id text,
  sellerId text,
  disputeReason text,
  buyerId text,
  itemId text,
  status text,
  decision text,
  arbitratorId text,
  skuId text,
  gmtCreated timestamp,
  gmtModified timestamp,
  item frozen<item>,
  resolution frozen<resolution>,
  PRIMARY KEY (id, itemId, gmtCreated));

CREATE TABLE disputes_changelog (
  id text,
  sellerId text,
  disputeReason text,
  buyerId text,
  itemId text,
  status text,
  arbitratorId text,
  skuId text,
  gmtCreated timestamp,
  gmtModified timestamp,
  item frozen<item>,
  resolution frozen<resolution>,
  PRIMARY KEY (id, gmtModified))
WITH CLUSTERING ORDER BY (gmtModified DESC);

CREATE MATERIALIZED VIEW disputes_by_seller_and_date AS
  SELECT * FROM disputes
  WHERE gmtCreated IS NOT NULL AND sellerid IS NOT NULL AND itemId IS NOT NULL AND id IS NOT NULL
  PRIMARY KEY (gmtCreated, sellerid, itemId, id);

CREATE MATERIALIZED VIEW disputes_by_buyer AS
  SELECT * FROM disputes
  WHERE gmtCreated IS NOT NULL AND buyerId IS NOT NULL AND itemId IS NOT NULL AND id IS NOT NULL
  PRIMARY KEY (gmtCreated, buyerId, itemId, id);

CREATE MATERIALIZED VIEW disputes_by_arbitrator AS
  SELECT * FROM disputes
  WHERE gmtCreated IS NOT NULL AND arbitratorId IS NOT NULL AND itemId IS NOT NULL AND id IS NOT NULL
  PRIMARY KEY (gmtCreated, arbitratorId, itemId, id);