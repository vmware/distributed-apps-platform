import React, { Component } from 'react'

import './Appdesign.css'
import {
  BrowserRouter as Router,
  Route,
  Redirect,
  Switch,
  Link,
} from "react-router-dom";
<<<<<<< HEAD
<<<<<<< HEAD
import { Layout, Menu} from 'antd';
import { LaptopOutlined, NotificationOutlined, AlertOutlined, CodeOutlined } from '@ant-design/icons';
=======
import { Layout, Menu, Breadcrumb } from 'antd';
import { UserOutlined, LaptopOutlined, NotificationOutlined, AlertOutlined, CodeOutlined } from '@ant-design/icons';
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
import { Layout, Menu} from 'antd';
import { LaptopOutlined, NotificationOutlined, AlertOutlined, CodeOutlined } from '@ant-design/icons';
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node

import Threats from './Threats/Threats';
import Setup from './Setup/Setup';
import Vulnerabilites from './Vulnerabilities/Vulnerabilities'
import Endpoint from './Endpoints/Endpoint'


<<<<<<< HEAD
<<<<<<< HEAD
=======
const { SubMenu } = Menu;
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
const { Header, Content, Sider } = Layout;


class Appdesign extends Component {
  constructor(props) {
    super(props);
    this.state = {};
  }
  render() {
    return (
      <div>
        <Router>
          <Layout>
            <Header className="header">
              <div className="logo" />
              <Menu theme="dark" mode="horizontal">
<<<<<<< HEAD
<<<<<<< HEAD
                <Menu.Item key="1" icon={<LaptopOutlined style={{ fontSize: 25 }} />} style={{ fontSize: 25 }}>LYDIAN</Menu.Item>
=======
                <Menu.Item key="1" icon={<LaptopOutlined style={{ fontSize: 25 }} />} style={{ fontSize: 25 }}>BORATHON</Menu.Item>
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
                <Menu.Item key="1" icon={<LaptopOutlined style={{ fontSize: 25 }} />} style={{ fontSize: 25 }}>LYDIAN</Menu.Item>
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
              </Menu>
            </Header>
            <Layout>
              <Sider width={200} className="site-layout-background">
                <Menu
                  mode="inline"
                  defaultSelectedKeys={['1']}
                  defaultOpenKeys={['sub1']}
                  style={{ height: '100%', borderRight: 0 }}
                >
                  <Menu.Item key="out1" icon={<CodeOutlined />}>
                    <Link to="/Setup">
                      Setup
            </Link>
                  </Menu.Item>
                  <Menu.Item key="out2" icon={<AlertOutlined />}>
                    <Link to="/Threats">
                      Threats
            </Link>
                  </Menu.Item>
                  <Menu.Item key="out3" icon={<NotificationOutlined />}>
                    <Link to="/Vulnerabilites">
                      Vulnerabilites
            </Link>
                  </Menu.Item>
                </Menu>
              </Sider>
              <Layout style={{ padding: '24px 24px 24px' }}>
                <Content
                  className="site-layout-background"
                  style={{
                    padding: 24,
                    margin: 0,
                    minHeight: 280,
                  }}
                >
                  <Switch>
                    <Route exact path="/Endpoint" component={Endpoint} />
                    <Route exact path="/Setup" component={Setup} />
                    <Route exact path="/Threats" component={Threats} />
                    <Route exact path="/Vulnerabilites" component={Vulnerabilites} />
                    <Redirect from="/" to="/Setup" />
                  </Switch>
                </Content>
              </Layout>
            </Layout>
          </Layout>
        </Router>
      </div>
    )
  }
}

<<<<<<< HEAD
<<<<<<< HEAD
export default Appdesign;
=======
export default Appdesign;
>>>>>>> ead4bbf... lydian-ui: Initial Lydian UI #Borathon2021
=======
export default Appdesign;
>>>>>>> 803fc3e... lydian-ui: adding edit option for primary node
