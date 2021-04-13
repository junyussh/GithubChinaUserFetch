import pandas as pd
from utils import FileWriter, GraphQL

class UserRepository:
    count = 0
    query = """
   {
  user(login: "%s") {
    repositories(last: %d, after: %s) {
      pageInfo {
        hasNextPage
        startCursor
        endCursor
      }
      edges {
        cursor
        node {
          name
          description
          url
          commitComments {
            totalCount
          }
          forkCount
          stargazerCount
          isArchived
          isFork
          issues {
            totalCount
          }
          diskUsage
          primaryLanguage {
            name
          }
          pullRequests {
            totalCount
          }
          pushedAt
          watchers {
            totalCount
          }
        }
      }
    }
  }
}

"""
    endCursor = "null"

    def __init__(self, login):
        self.data = {}
        self.reform = []
        self.df = None
        self.login = login

    def fetch(self, num=10, batch_size=10):
        times = int(num/batch_size)
        if times < 1:
            times = 1
        print("data numbers: %d" % num)
        print("batch_size: %d" % batch_size)
        # times = num
        rest = num % batch_size
        if rest > 0 and times != 1:
            times = times+1
        print("times: %d" % times)
        for i in range(times):
            # print(self.query % self.endCursor)
            print("Request #%d" % (i+1))
            # print(self.endCursor)
            if i == times-1 and rest > 0:
                query = self.query % (self.login, rest, self.endCursor)
            else:
                query = self.query % (self.login, batch_size, self.endCursor)
            data = GraphQL.execute(query)
            if self.data:
                self.data["user"]["repositories"]["edges"] = self.data["user"]["repositories"]["edges"] + data["user"]["repositories"]["edges"]
                self.data["user"]["repositories"]["pageInfo"] = self.data["user"]["repositories"]["pageInfo"]
            else:
                self.data = data
            print("Finshed #%d" % (i+1))
            # print(data)
            self.endCursor = "\"%s\"" % data["user"]["repositories"]["pageInfo"]["endCursor"]

    def preprocessing(self):
        print("Data preprocessing")
        # print(self.data)
        if self.data:
            self.reform = self.data["user"]["repositories"]["edges"]
            cursors = list(map(lambda x: x["cursor"], self.reform))
            self.reform = list(map(lambda x: x["node"], self.reform))
            for (index, i) in enumerate(self.reform):
                # print(self.reform[index])
                self.reform[index]["commitComments"] = i["commitComments"]["totalCount"]
                self.reform[index]["issues"] = i["issues"]["totalCount"]
                self.reform[index]["pullRequests"] = i["pullRequests"]["totalCount"]
                self.reform[index]["watchers"] = i["watchers"]["totalCount"]
                if i["primaryLanguage"]:
                  self.reform[index]["primaryLanguage"] = i["primaryLanguage"]["name"]
                self.reform[index]["cursor"] = cursors[index]
                if i["description"]:
                    self.reform[index]["description"] = i["description"].replace('\n', '').replace('\r', '')

    def toDataFrame(self):
        self.preprocessing()
        self.df = pd.json_normalize(self.reform)
        self.df["login"] = self.login
        print(self.df)

    def saveCSV(self, fileName, mode):
        print("Save data")
        FileWriter.writeFile(self.df, fileName, mode)
