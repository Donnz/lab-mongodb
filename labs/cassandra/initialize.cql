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
  PRIMARY KEY (id));

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



